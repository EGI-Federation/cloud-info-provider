#!/usr/bin/groovy

pipeline {
    agent {
        label 'python'
    }

    stages {
        stage('Style Analysis') {
            steps {
                checkout scm
                echo 'Running flake8..'
                timeout(time: 5, unit: 'MINUTES') {
                    sh 'tox -e pep8'
                    echo 'Parsing pep8 logs..'
                    step([$class: 'WarningsPublisher',
                        parserConfigurations: [[
                            parserName: 'Pep8', pattern: '.tox/pep8/log/*.log'
                        ]], unstableTotalAll: '0', usePreviousBuildAsReference: true
                    ])
                }
            }
        }

        stage('Unit tests') {
            steps {
                checkout scm
                echo 'Computing unit testing coverage..'
                sh 'tox -e cover'

                echo 'Generating Cobertura report..'
                sh 'tox -e cobertura'
                cobertura autoUpdateHealth: false,
                          autoUpdateStability: false,
                          coberturaReportFile: '**/coverage.xml',
                          conditionalCoverageTargets: '70, 0, 0',
                          failUnhealthy: false,
                          failUnstable: false,
                          lineCoverageTargets: '80, 0, 0',
                          maxNumberOfBuilds: 0,
                          methodCoverageTargets: '80, 0, 0',
                          onlyStable: false,
                          sourceEncoding: 'ASCII',
                          zoomCoverageChart: false
            }
        }

        stage('Build RPM/DEB packages') {
            when {
                anyOf {
                    buildingTag()
                    branch 'master'
                }
            }
            parallel {
                stage('Build on Ubuntu16.04') {
                    agent {
                        label 'bubuntu16'
                    }
                    steps {
                        checkout scm
                        echo 'Within build on Ubuntu16.04'   
                            sh 'sudo apt-get update && sudo apt-get install -y devscripts debhelper python-all-dev python-pbr python-setuptools'
                            sh 'debuild --no-tgz-check clean binary'
                        dir("${WORKSPACE}/debs/cloud-info-provider-openstack") {
                            sh 'debuild --no-tgz-check clean binary'
                        }
                        dir("${WORKSPACE}/debs/cloud-info-provider-opennebula") {
                            sh 'debuild --no-tgz-check clean binary'
                        }
                    }
                    post {
                        success {
                            archiveArtifacts artifacts: '**/debs/*.deb'                        }
                    }
                }
                stage('Build on CentOS7') {
                    agent {
                        label 'bcentos7'
                    }
                    steps {
                        checkout scm
                        echo 'Within build on CentOS7'
                        sh 'sudo yum install -y rpm-build centos-release-openstack-newton python-pbr python-setuptools'
                        sh 'python setup.py sdist'
                        sh 'mkdir ~/rpmbuild'
                        sh "echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros"
                        sh 'mkdir -p ~/rpmbuild/{SOURCES,SPECS}'
                        sh 'cp dist/cloud_info_provider*.tar.gz ~/rpmbuild/SOURCES/'
                        sh 'cp rpm/cloud-info-provider*.spec ~/rpmbuild/SPECS/'
                        sh 'rpmbuild --define "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider.spec'
                        sh 'rpmbuild "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider-openstack.spec'
                        sh 'rpmbuild "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider-opennebula.spec'
                        sh 'cp ~/rpmbuild/SRPMS/*.rpm ~/rpmbuild/RPMS/noarch/*.rpm ${WORKSPACE}/rpm/'
                    }
                    post {
                        success {
                            archiveArtifacts artifacts: '**/rpm/*.rpm'
                        }
                    }
                }
            }
        }

       	stage('Notifications') {
            when {
                buildingTag()
            }
            steps {
                JiraIssueNotification(
                    'DEEP',
                    'DPM',
                    '10204',
                    "[preview-testbed] New cloud-info-provider version ${env.BRANCH_NAME} available",
                    "Check new artifacts at:\n\t- RPMs/DEBs: ${env.BUILD_URL}\n",
                    ['wp3', 'preview-testbed', "DEEPaaS-${env.BRANCH_NAME}"],
                    'Task',
                    'mariojmdavid'
                )
            }
        }
    }
}
