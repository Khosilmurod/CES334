echo "starting script"
cp *config.txt /student334/CES334/raspberrypi/configs/
hostname -I | awk '{print $1}' > ~/CES334/raspberrypi/configs/ip.md
git add .
git commit -m"updated config files and ip"
git push