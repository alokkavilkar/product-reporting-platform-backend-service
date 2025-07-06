def IMAGE_NAME = "alokkavilkar227/report-platform-backend-service:1.0"

node('node1'){
    stage('checkout') {
        checkout scm
    }

    stage('Environment setup for test'){
        sh "docker build -t ${IMAGE_NAME}-test -f Dockerfile.test ."
    }

    stage('Run Django Tests') {

        withCredentials([
            usernamePassword(credentialsId: 'aiven-db-credentials', usernameVariable: 'TEST_DB_USER', passwordVariable: 'TEST_DB_PASSWORD'),
            string(credentialsId: 'django-pdi-app-secret', variable: 'DJANGO_SECRET_KEY'),
            string(credentialsId: 'AUTH0-ROLE-NAMESPACE', variable: 'ROLE_NAMESPACE')
        ])
        {
            sh """
                export TEST_DB_USER=${TEST_DB_USER}
                export TEST_DB_PASSWORD=${TEST_DB_PASSWORD}

                docker run -v ${env.WORKSPACE}/coverage:/app/htmlcov --rm \
                -e DEV=True \
                -e TEST_DB_NAME=defaultdb \
                -e TEST_DB_USER=\$TEST_DB_USER \
                -e TEST_DB_PASSWORD=\$TEST_DB_PASSWORD \
                -e TEST_DB_HOST=pg-f205f26-alokkavilkar-dc92.c.aivencloud.com \
                -e TEST_DB_PORT=16997 \
                -e TEST_DB_SSLMODE=require \
                -e SECRET_KEY=\$DJANGO_SECRET_KEY \
                -e DJANGO_SETTINGS_MODULE=core.settings_test \
                -e ROLE_NAMESPACE=\$ROLE_NAMESPACE \
                ${IMAGE_NAME}-test pytest
            """
        }
    }

    stage('Security test') {

        withCredentials([
            usernamePassword(credentialsId: 'aiven-db-credentials', usernameVariable: 'TEST_DB_USER', passwordVariable: 'TEST_DB_PASSWORD'),
            string(credentialsId: 'django-pdi-app-secret', variable: 'DJANGO_SECRET_KEY'),
            string(credentialsId: 'AUTH0-ROLE-NAMESPACE', variable: 'ROLE_NAMESPACE')
        ])
        {
            echo "Bandit security checking"
            sh """
                export TEST_DB_USER=${TEST_DB_USER}
                export TEST_DB_PASSWORD=${TEST_DB_PASSWORD}

                docker run -v ${env.WORKSPACE}/coverage:/app/htmlcov --rm \
                -e DEV=True \
                -e TEST_DB_NAME=defaultdb \
                -e TEST_DB_USER=\$TEST_DB_USER \
                -e TEST_DB_PASSWORD=\$TEST_DB_PASSWORD \
                -e TEST_DB_HOST=pg-f205f26-alokkavilkar-dc92.c.aivencloud.com \
                -e TEST_DB_PORT=16997 \
                -e TEST_DB_SSLMODE=require \
                -e SECRET_KEY=\$DJANGO_SECRET_KEY \
                -e DJANGO_SETTINGS_MODULE=core.settings_test \
                -e ROLE_NAMESPACE=\$ROLE_NAMESPACE \
                ${IMAGE_NAME}-test sh -c "
                mkdir -p security-reports/
                bandit -r . -f xml -o security-reports/bandit.xml || true
                "
            """

            echo "Dependecies safety checking"

             sh """
                export TEST_DB_USER=${TEST_DB_USER}
                export TEST_DB_PASSWORD=${TEST_DB_PASSWORD}

                docker run -v ${env.WORKSPACE}/coverage:/app/htmlcov --rm \
                -e DEV=True \
                -e TEST_DB_NAME=defaultdb \
                -e TEST_DB_USER=\$TEST_DB_USER \
                -e TEST_DB_PASSWORD=\$TEST_DB_PASSWORD \
                -e TEST_DB_HOST=pg-f205f26-alokkavilkar-dc92.c.aivencloud.com \
                -e TEST_DB_PORT=16997 \
                -e TEST_DB_SSLMODE=require \
                -e SECRET_KEY=\$DJANGO_SECRET_KEY \
                -e DJANGO_SETTINGS_MODULE=core.settings_test \
                -e ROLE_NAMESPACE=\$ROLE_NAMESPACE \
                ${IMAGE_NAME}-test sh -c "
                pip freeze > requirements.freeze.txt
                safety check --file=requirements.freeze.txt --full-report --output=json > security-reports/safety.json
                "
            """
        }
    }
}