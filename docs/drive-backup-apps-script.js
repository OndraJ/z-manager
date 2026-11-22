/**
 * Zuza's Manager – copy backup e-mail attachments to Google Drive.
 *
 * Runs as a Google Apps Script in the app's Gmail account (zuzasmanager@gmail.com).
 * The app sends backups via this account's SMTP, so every backup is in its "Sent" mail.
 * This script finds backup e-mails it has not processed yet, saves the attached
 * `zuzas-manager-*.sqlite3` files into a Drive folder and labels the e-mails as done.
 *
 * Setup: see docs/drive-backup.md. Version-controlled here; the live copy is in
 * script.google.com – paste this file there after changing it.
 */

const FOLDER_NAME = "Zuza's Manager Backups";
const DONE_LABEL = "zuzas-manager-backup-saved";
const SEARCH_QUERY = `from:me filename:sqlite3 has:attachment -label:${DONE_LABEL}`;
const ATTACHMENT_PATTERN = /^zuzas-manager-.*\.sqlite3$/;
const MAX_THREADS_PER_RUN = 50;

/** Main function – run by the hourly trigger (or manually). */
function saveBackupsToDrive() {
  const folder = getOrCreateFolder_(FOLDER_NAME);
  const label = GmailApp.getUserLabelByName(DONE_LABEL) || GmailApp.createLabel(DONE_LABEL);
  const threads = GmailApp.search(SEARCH_QUERY, 0, MAX_THREADS_PER_RUN);
  let saved = 0;

  threads.forEach((thread) => {
    thread.getMessages().forEach((message) => {
      message.getAttachments().forEach((attachment) => {
        const name = attachment.getName();
        if (!ATTACHMENT_PATTERN.test(name)) return;
        // Idempotent: a file with the same name (date + time) is saved only once.
        if (folder.getFilesByName(name).hasNext()) return;
        folder.createFile(attachment.copyBlob().setName(name));
        saved += 1;
      });
    });
    thread.addLabel(label);
  });

  console.log(`Processed ${threads.length} e-mail thread(s), saved ${saved} new backup(s).`);
}

/** Run once by hand: creates the hourly trigger (safe to run again). */
function setupTrigger() {
  const exists = ScriptApp.getProjectTriggers().some(
    (trigger) => trigger.getHandlerFunction() === "saveBackupsToDrive"
  );
  if (!exists) {
    ScriptApp.newTrigger("saveBackupsToDrive").timeBased().everyHours(1).create();
  }
  console.log(exists ? "Trigger already exists." : "Hourly trigger created.");
  saveBackupsToDrive();
}

function getOrCreateFolder_(name) {
  const folders = DriveApp.getFoldersByName(name);
  return folders.hasNext() ? folders.next() : DriveApp.createFolder(name);
}
