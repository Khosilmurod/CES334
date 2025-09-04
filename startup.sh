echo "starting script"
cp /boot/firmware/config.txt ./config
hostname -I | awk '{print $1}' > ./ip.md
git add .
git commit -m"updated config files and ip"
git push