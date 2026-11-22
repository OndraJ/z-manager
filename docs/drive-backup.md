# Backups on Google Drive

The app e-mails backups (see README → Backups). It sends them through the app's own Gmail account `zuzasmanager@gmail.com`, so a copy of every backup lands in that account's **Sent** mail. A small Google Apps Script in the same account copies the attachments into a Drive folder **"Zuza's Manager Backups"** once an hour.

Nothing in the app needs to change and no Google credentials are stored on Zuza's laptop. If the script ever stops working, backups still arrive by e-mail.

Script source: [`drive-backup-apps-script.js`](drive-backup-apps-script.js).

## Setup (once, in a browser)

1. Sign in to Google as `zuzasmanager@gmail.com` and open <https://script.google.com>.
2. **New project** → rename it to `Zuza's Manager – Drive backups`.
3. Replace the content of `Code.gs` with `docs/drive-backup-apps-script.js` and save (Ctrl+S).
4. In the toolbar choose the function **`setupTrigger`** and click **Run**.
5. Authorize the script:
   - *Review permissions* → choose `zuzasmanager@gmail.com`.
   - Google warns *„Google hasn’t verified this app“* – that is expected for your own script: **Advanced** → **Go to … (unsafe)** → **Allow** (Gmail + Drive access).
6. The execution log should end with `Hourly trigger created.` and `Processed … saved …`. The Drive folder is created on the first run.
7. Optional: share the folder with Zuza (Drive → right-click the folder → Share → her address, *Viewer*).

## How it works

- Search: `from:me filename:sqlite3 has:attachment -label:zuzas-manager-backup-saved`.
- Every attachment named `zuzas-manager-*.sqlite3` is saved to the folder (each backup has a unique date-time name, so nothing is overwritten). Processed e-mails get the Gmail label `zuzas-manager-backup-saved`.
- Runs every hour; to test right away, click „Zálohovat“ in the app and run `saveBackupsToDrive` manually in the script editor.

## Troubleshooting

- **Nothing is saved:** the script only sees backups *sent from* `zuzasmanager@gmail.com`. Check that `EMAIL_HOST_USER` in `.env` on Zuza's laptop is `zuzasmanager@gmail.com` and that the backup e-mail is in that account's *Sent* folder.
- **Errors:** script editor → *Executions* shows the log of every run. Google also e-mails the account when a triggered run fails.
- **Restore:** download the file from the Drive folder and follow README → Restoring from a backup.
