#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@1.3.5']) _

pipeline {
    agent {
        label 'python'
    }

    stages {
        stage('Code fetching') {
            steps {
                checkout scm
            }
        }

        stage('Style analysis') {
            steps {
                ToxEnvRun('pep8')
            }
            post {
                always {
                    WarningsReport('Pep8')
                }
            }
        }

        stage('Unit testing coverage') {
            steps {
                ToxEnvRun('cover')
                ToxEnvRun('cobertura')
            }
            post {
                success {
                    HTMLReport('cover', 'index.html', 'coverage.py report')
                    CoberturaReport('**/coverage.xml')
                }
            }
        }

        stage('Metrics gathering') {
            agent {
                label 'sloc'
            }
            steps {
                checkout scm
                SLOCRun()
            }
            post {
                success {
                    SLOCPublish()
                }
            }
        }

        stage('Security scanner') {
            steps {
                ToxEnvRun('bandit-report')
                script {
                    if (currentBuild.result == 'FAILURE') {
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
            post {
                always {
                    HTMLReport("/tmp/bandit", 'index.html', 'Bandit report')
                }
            }
        }

        stage('Build RPM/DEB packages') {
            when {
                anyOf {
                    buildingTag()
                }
            }
            parallel {
                stage('Build on Ubuntu18.04') {
                    agent {
                        label 'bubuntu18'
                    }
                    steps {
                        checkout scm
                        echo 'Within build on Ubuntu18.04'
                        sh 'debuild --no-tgz-check -- clean binary'
                        sh 'cp ../*.deb debs/'
                        dir("${WORKSPACE}/debs/cloud-info-provider-deep-openstack") {
                            sh 'debuild --no-tgz-check -- clean binary'
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
                        sh 'sudo yum --enablerepo=extras install -y epel-release && sudo yum clean all && sudo yum makecache fast'
                        sh 'sudo yum install -y rpm-build centos-release-openstack-newton python-pbr python-setuptools'
                        sh 'python setup.py sdist'
                        sh 'mkdir ~/rpmbuild'
                        sh "echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros"
                        sh 'mkdir -p ~/rpmbuild/{SOURCES,SPECS}'
                        sh 'cp dist/cloud_info_provider*.tar.gz ~/rpmbuild/SOURCES/'
                        sh 'cp rpm/cloud-info-provider*.spec ~/rpmbuild/SPECS/'
                        sh 'rpmbuild --define "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider.spec'
                        sh 'rpmbuild --define "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider-openstack.spec'
                        //sh 'rpmbuild --define "_pbr_version $(python setup.py --version)" -ba ~/rpmbuild/SPECS/cloud-info-provider-opennebula.spec'
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
                    'mariojmdavid',
                    ['wgcastell',
                     'vkozlov',
                     'dlugo',
                     'keiichiito',
                     'laralloret',
                     'ignacioheredia']
                )
            }
        }
    }
}
