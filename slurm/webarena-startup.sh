WA_SCRIPTS_BASE="/nlpgpu/data/andrz/webarena-setup/webarena"
pushd $WA_SCRIPTS_BASE

bash 01_docker_load_images.sh
bash 02_docker_remove_containers.sh
bash 03_docker_create_containers.sh
bash 04_docker_start_containers.sh
bash 05_docker_patch_containers.sh
bash 06_serve_homepage.sh &
bash 07_serve_reset.sh &

popd
