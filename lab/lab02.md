# Lab Notes #2

## Systemd and Config File Backup

- [x] I automated uploading so that every time the system boots, the script is run and the IP uploaded to GitHub.  
  - First, I fixed `startup.sh` so it correctly updated `ip.md` and pushed it to GitHub when run manually.  
  - I then created a systemd service file (`/etc/systemd/system/startup.service`) that calls the script on boot.  
  - After writing the service, I reloaded systemd and enabled it so it runs automatically:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable startup.service
    sudo systemctl start startup.service
    ```
  - Verified that after reboot, the IP is automatically uploaded.

---

## SCP File Copy for Backup to Remote Server or Laptop

- [x] I first tested SCP manually by copying `ip.md` from the Pi to my Mac laptop.  
  - Example test command:
    ```bash
    scp student334@<Pi-IP>:/home/student334/Desktop/ces334-225/CES334/ip.md /Users/<mac-username>/Desktop/
    ```

- [x] After confirming manual copy worked, I set up SSH key authentication so I wouldn’t need to type the password every time.  
  - Generated a key on the Pi and copied it to my Mac’s `authorized_keys`.  
  - Tested that I could run `scp` without being prompted for a password.

- [x] I added a cron job on the Pi that runs every 10 minutes to run scp command!
