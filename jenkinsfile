pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        DEPLOY_DIR = '/opt/employee-app'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm

                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    set -eu
                    docker build \
                      -t employee-web:$IMAGE_TAG .
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    set -eu
                    docker run --rm \
                      employee-web:$IMAGE_TAG \
                      python -m unittest discover -s /tests -v
                '''
            }
        }

        stage('Prepare Deployment') {
            steps {
                sh '''
                    set -eu

                    cp compose.yaml "$DEPLOY_DIR/compose.yaml"
                    mkdir -p "$DEPLOY_DIR/database"
                    cp database/init.sql "$DEPLOY_DIR/database/init.sql"

                    docker compose \
                      --env-file "$DEPLOY_DIR/.env" \
                      -f "$DEPLOY_DIR/compose.yaml" \
                      config --quiet

                    if [ -f "$DEPLOY_DIR/current-image-tag" ]; then
                      cp "$DEPLOY_DIR/current-image-tag" \
                         "$DEPLOY_DIR/previous-image-tag"
                    fi
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -eu

                    docker compose \
                      --env-file "$DEPLOY_DIR/.env" \
                      -f "$DEPLOY_DIR/compose.yaml" \
                      up -d --wait --wait-timeout 240
                '''
            }
        }

        stage('Verify Application') {
            steps {
                sh '''
                    set -eu

                    curl --fail --silent --show-error \
                      --retry 12 --retry-delay 5 --retry-connrefused \
                      http://127.0.0.1/ready

                    curl --fail --silent --show-error \
                      http://127.0.0.1/ \
                      | grep -q 'Employee Manager'

                    printf '%s\\n' "$IMAGE_TAG" \
                      > "$DEPLOY_DIR/current-image-tag"
                '''
            }
        }
    }

    post {
        success {
            echo 'Application deployed and verified successfully.'
        }

        failure {
            echo 'Build or deployment failed. Check the stage and logs.'
        }

        always {
            sh '''
                docker compose \
                  --env-file "$DEPLOY_DIR/.env" \
                  -f "$DEPLOY_DIR/compose.yaml" \
                  logs --no-color --tail=100 \
                  > deployment-logs.txt 2>&1 || true
            '''

            archiveArtifacts(
                artifacts: 'deployment-logs.txt',
                allowEmptyArchive: true
            )
        }
    }
}
