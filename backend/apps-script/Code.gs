/**
 * Fluid Silicon website forms: demo requests, contact messages and job applications.
 *
 * One Apps Script web app receives all three forms from fluidsilicon.com, writes each
 * submission to a Google Sheet, stores résumés in a private Drive folder and emails
 * the team. The site posts JSON with no Content-Type header (a "simple" request, so
 * browsers send no CORS preflight) and expects {"status":"ok"} back.
 *
 * Set up (about ten minutes):
 *   1. Create a Google Sheet, open Extensions > Apps Script, and paste this file in.
 *   2. Edit CONFIG below (notification addresses, retention periods).
 *   3. Run setup() once from the editor and accept the permissions prompt.
 *      It creates the "Demo requests", "Contact messages" and "Applications" tabs and the résumé folder.
 *   4. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone.
 *   5. Put the /exec URL in src/assets/js/config.js as demoEndpoint and applyEndpoint,
 *      rebuild, and publish. Send one test of each form.
 *   6. Optional: run installRetentionTrigger() once to delete old submissions daily.
 *
 * After editing this file later, use Deploy > Manage deployments > Edit > New version,
 * so the /exec URL stays the same.
 */

const CONFIG = {
  SHEET_ID: '',                             // empty: use the spreadsheet this script is bound to
  NOTIFY_DEMO: 'info@fluidsilicon.com',     // who hears about demo requests (comma-separate several)
  NOTIFY_APPLY: 'careers@fluidsilicon.com', // who hears about applications
  SEND_RECEIPTS: true,                      // short confirmation email to the person who submitted
  REPLY_DAYS_DEMO: 2,                       // keep in step with replyDays in config.js
  REPLY_DAYS_APPLY: 5,                      // keep in step with the careers and apply pages
  MAX_RESUME_MB: 5,                         // keep in step with maxResumeMB in config.js
  MIN_ELAPSED_MS: 2500,                     // a form finished faster than this is treated as a bot
  DUPLICATE_WINDOW_S: 120,                  // same email and form inside this window is saved once
  RETENTION_DAYS_DEMO: 0,                   // 0 keeps everything; match the privacy notice before enabling
  RETENTION_DAYS_APPLY: 0,
};

const TABS = {
  demo: {
    name: 'Demo requests',
    headers: ['Received', 'Name', 'Work email', 'Company', 'Role', 'FPGA families', 'Fleet size', 'Industry',
              'Priorities', 'Timeline', 'Message', 'Consent', 'Page', 'Status', 'Notes'],
  },
  contact: {
    name: 'Contact messages',
    headers: ['Received', 'Name', 'Work email', 'Company', 'Topic', 'Message', 'Consent', 'Page', 'Status', 'Notes'],
  },
  application: {
    name: 'Applications',
    headers: ['Received', 'Name', 'Email', 'Phone', 'Location', 'Role', 'Earliest start', 'On-site in Philadelphia',
              'School', 'Expected graduation', 'LinkedIn', 'GitHub or portfolio', 'Note', 'Authorized to work in US',
              'Needs sponsorship', 'Résumé', 'Résumé file ID', 'Status', 'Notes'],
  },
};

const RESUME_TYPES = {
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
};

/* ------------------------------------------------------------------ entry points */

function doPost(e) {
  let data;
  try {
    data = parseBody_(e);
  } catch (err) {
    return reply_('error', 'The form data could not be read.');
  }
  // Bots: accept quietly so they learn nothing, but store nothing.
  if (data.honeypot || data.website) return reply_('ok');
  if (typeof data.elapsedMs === 'number' && data.elapsedMs < CONFIG.MIN_ELAPSED_MS) return reply_('ok');

  const type = data.formType === 'demo' ? 'demo' : data.formType === 'contact' ? 'contact'
    : (data.formType === 'application' || data.fileData) ? 'application' : '';
  if (!type) return reply_('error', 'Unknown form.');

  const problem = type === 'demo' ? checkDemo_(data) : type === 'contact' ? checkContact_(data) : checkApplication_(data);
  if (problem) return reply_('error', problem);

  if (seenRecently_(type, data.email)) return reply_('ok');     // double-click or resubmit: saved once

  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    if (type === 'demo') saveDemo_(data); else if (type === 'contact') saveContact_(data); else saveApplication_(data);
    markSeen_(type, data.email);
  } catch (err) {
    console.error(err && err.stack || err);
    return reply_('error', 'We could not save that just now. Please try again, or email us.');
  } finally {
    try { lock.releaseLock(); } catch (ignored) {}
  }
  try {
    if (type === 'demo') notifyDemo_(data); else if (type === 'contact') notifyContact_(data); else notifyApplication_(data);
  } catch (err) {
    console.error('notify failed', err && err.stack || err);   // the row is saved; do not fail the visitor
  }
  return reply_('ok');
}

function doGet() {
  return reply_('ok', 'Fluid Silicon forms endpoint. Submissions are accepted by POST only.');
}

/** Run once from the editor: creates tabs, the résumé folder and stores their IDs. */
function setup() {
  const ss = spreadsheet_();
  Object.keys(TABS).forEach(function (k) { sheet_(ss, k); });
  const folder = resumeFolder_();
  console.log('Sheet: ' + ss.getUrl());
  console.log('Résumé folder: ' + folder.getUrl() + ' (share it with the hiring team only)');
}

/** Optional: deletes rows and résumés older than the retention periods in CONFIG, daily. */
function installRetentionTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'purgeOldSubmissions') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('purgeOldSubmissions').timeBased().everyDays(1).atHour(3).create();
}

function purgeOldSubmissions() {
  const ss = spreadsheet_();
  purgeTab_(sheet_(ss, 'demo'), CONFIG.RETENTION_DAYS_DEMO, -1);
  purgeTab_(sheet_(ss, 'contact'), CONFIG.RETENTION_DAYS_DEMO, -1);
  purgeTab_(sheet_(ss, 'application'), CONFIG.RETENTION_DAYS_APPLY, TABS.application.headers.indexOf('Résumé file ID'));
}

/* ------------------------------------------------------------------ validation */

function checkDemo_(d) {
  if (!clean_(d.name)) return 'Enter your name.';
  if (!isEmail_(d.email)) return 'Enter a valid work email.';
  if (!clean_(d.company)) return 'Enter your company.';
  if (d.consent !== true && d.consent !== 'true' && d.consent !== 'on') return 'Consent is needed so we can contact you.';
  return '';
}

function checkContact_(d) {
  if (!clean_(d.name)) return 'Enter your name.';
  if (!isEmail_(d.email)) return 'Enter a valid work email.';
  if (!clean_(d.message)) return 'Tell us what this is about.';
  if (d.consent !== true && d.consent !== 'true' && d.consent !== 'on') return 'Consent is needed so we can reply to you.';
  return '';
}

function checkApplication_(d) {
  if (!clean_(d.name)) return 'Enter your full name.';
  if (!isEmail_(d.email)) return 'Enter a valid email address.';
  if (!clean_(d.role)) return 'Choose a role.';
  if (!d.fileData || !d.fileName) return 'Attach your résumé.';
  const ext = String(d.fileName).split('.').pop().toLowerCase();
  if (!RESUME_TYPES[ext]) return 'Use a PDF, DOC or DOCX file.';
  const bytes = Math.floor(String(d.fileData).length * 3 / 4);
  if (bytes > CONFIG.MAX_RESUME_MB * 1024 * 1024) return 'Keep the résumé under ' + CONFIG.MAX_RESUME_MB + ' MB.';
  return '';
}

/* ------------------------------------------------------------------ storage */

function saveDemo_(d) {
  const sh = sheet_(spreadsheet_(), 'demo');
  sh.appendRow([
    new Date(), cell_(d.name), cell_(d.email), cell_(d.company), cell_(d.title), cell_(list_(d.families)),
    cell_(d.fleetSize), cell_(d.industry), cell_(list_(d.goals)), cell_(d.timeline), cell_(d.message, 5000),
    d.consent ? 'Yes' : 'No', cell_(d.page), 'New', '',
  ]);
}

function saveContact_(d) {
  const sh = sheet_(spreadsheet_(), 'contact');
  sh.appendRow([
    new Date(), cell_(d.name), cell_(d.email), cell_(d.company), cell_(d.topic), cell_(d.message, 5000),
    d.consent ? 'Yes' : 'No', cell_(d.page), 'New', '',
  ]);
}

function saveApplication_(d) {
  const ext = String(d.fileName).split('.').pop().toLowerCase();
  const blob = Utilities.newBlob(Utilities.base64Decode(String(d.fileData)), RESUME_TYPES[ext],
    safeName_(Utilities.formatDate(new Date(), 'Etc/UTC', 'yyyy-MM-dd') + ' ' + clean_(d.name) + ' - ' + clean_(d.role) + '.' + ext));
  const file = resumeFolder_().createFile(blob);
  d._resumeUrl = file.getUrl();
  d._resumeId = file.getId();
  const sh = sheet_(spreadsheet_(), 'application');
  sh.appendRow([
    new Date(), cell_(d.name), cell_(d.email), cell_(d.phone), cell_(d.location), cell_(d.role), cell_(d.startDate),
    cell_(d.onsite), cell_(d.school), cell_(d.graduation), cell_(d.linkedin), cell_(d.portfolio), cell_(d.coverLetter, 10000),
    cell_(d.workAuthorized), cell_(d.needSponsorship), d._resumeUrl, d._resumeId, 'New', '',
  ]);
}

function purgeTab_(sh, days, fileCol) {
  if (!days || days <= 0) return;
  const cutoff = Date.now() - days * 86400000;
  const values = sh.getDataRange().getValues();
  for (let r = values.length - 1; r >= 1; r--) {           // bottom-up so row numbers stay valid
    const when = values[r][0];
    if (when instanceof Date && when.getTime() < cutoff) {
      if (fileCol >= 0 && values[r][fileCol]) {
        try { DriveApp.getFileById(values[r][fileCol]).setTrashed(true); } catch (ignored) {}
      }
      sh.deleteRow(r + 1);
    }
  }
}

/* ------------------------------------------------------------------ email */

function notifyDemo_(d) {
  const lines = [
    'Name: ' + clean_(d.name), 'Email: ' + clean_(d.email), 'Company: ' + clean_(d.company), 'Role: ' + clean_(d.title),
    'FPGA families: ' + list_(d.families), 'Fleet size: ' + clean_(d.fleetSize), 'Industry: ' + clean_(d.industry),
    'Priorities: ' + list_(d.goals), 'Timeline: ' + clean_(d.timeline), '', clean_(d.message, 5000),
  ];
  MailApp.sendEmail({
    to: CONFIG.NOTIFY_DEMO, replyTo: clean_(d.email),
    subject: 'Demo request: ' + clean_(d.company) + ' (' + clean_(d.name) + ')',
    body: lines.join('\n') + '\n\nSaved to: ' + spreadsheet_().getUrl(),
  });
  if (CONFIG.SEND_RECEIPTS) {
    MailApp.sendEmail({
      to: clean_(d.email), replyTo: CONFIG.NOTIFY_DEMO.split(',')[0], name: 'Fluid Silicon',
      subject: 'We received your demo request',
      body: 'Hi ' + firstName_(d.name) + ',\n\nThanks for your interest in Fluid Silicon. We received your demo request and will reply within ' +
        days_(CONFIG.REPLY_DAYS_DEMO) + ' to set a time.\n\nIf anything changes, reply to this email.\n\nFluid Silicon\nhttps://fluidsilicon.com',
    });
  }
}

function notifyContact_(d) {
  const lines = ['Topic: ' + clean_(d.topic), 'Name: ' + clean_(d.name), 'Email: ' + clean_(d.email), 'Company: ' + clean_(d.company), '', clean_(d.message, 5000)];
  MailApp.sendEmail({
    to: CONFIG.NOTIFY_DEMO, replyTo: clean_(d.email),
    subject: 'Contact (' + clean_(d.topic) + '): ' + (clean_(d.company) || clean_(d.name)),
    body: lines.join('\n') + '\n\nSaved to: ' + spreadsheet_().getUrl(),
  });
  if (CONFIG.SEND_RECEIPTS) {
    MailApp.sendEmail({
      to: clean_(d.email), replyTo: CONFIG.NOTIFY_DEMO.split(',')[0], name: 'Fluid Silicon',
      subject: 'We received your message',
      body: 'Hi ' + firstName_(d.name) + ',\n\nThanks for writing to Fluid Silicon. We received your message and will reply within ' +
        days_(CONFIG.REPLY_DAYS_DEMO) + '.\n\nFluid Silicon\nhttps://fluidsilicon.com',
    });
  }
}

function notifyApplication_(d) {
  const lines = [
    'Role: ' + clean_(d.role), 'Name: ' + clean_(d.name), 'Email: ' + clean_(d.email), 'Phone: ' + clean_(d.phone),
    'Based in: ' + clean_(d.location), 'Earliest start: ' + clean_(d.startDate), 'On-site: ' + clean_(d.onsite),
    'School: ' + clean_(d.school), 'Graduation: ' + clean_(d.graduation), 'LinkedIn: ' + clean_(d.linkedin),
    'Portfolio: ' + clean_(d.portfolio), 'Authorized to work in US: ' + clean_(d.workAuthorized),
    'Needs sponsorship: ' + clean_(d.needSponsorship), 'Résumé: ' + (d._resumeUrl || ''), '', clean_(d.coverLetter, 10000),
  ];
  MailApp.sendEmail({
    to: CONFIG.NOTIFY_APPLY, replyTo: clean_(d.email),
    subject: 'Application: ' + clean_(d.role) + ' - ' + clean_(d.name),
    body: lines.join('\n') + '\n\nAll applications: ' + spreadsheet_().getUrl(),
  });
  if (CONFIG.SEND_RECEIPTS) {
    MailApp.sendEmail({
      to: clean_(d.email), replyTo: CONFIG.NOTIFY_APPLY.split(',')[0], name: 'Fluid Silicon',
      subject: 'We received your application',
      body: 'Hi ' + firstName_(d.name) + ',\n\nThank you for applying for ' + clean_(d.role) + ' at Fluid Silicon. An engineer on the team will read your application, and we will reply within ' +
        days_(CONFIG.REPLY_DAYS_APPLY) + '.\n\nFluid Silicon\nhttps://fluidsilicon.com/careers/',
    });
  }
}

/* ------------------------------------------------------------------ helpers */

function parseBody_(e) {
  if (!e || !e.postData || !e.postData.contents) throw new Error('empty body');
  const d = JSON.parse(e.postData.contents);
  if (!d || typeof d !== 'object' || Array.isArray(d)) throw new Error('not an object');
  return d;
}

function reply_(status, message) {
  const body = { status: status };
  if (message) body.message = message;
  return ContentService.createTextOutput(JSON.stringify(body)).setMimeType(ContentService.MimeType.JSON);
}

function spreadsheet_() {
  return CONFIG.SHEET_ID ? SpreadsheetApp.openById(CONFIG.SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
}

function sheet_(ss, key) {
  const t = TABS[key];
  let sh = ss.getSheetByName(t.name);
  if (!sh) {
    sh = ss.insertSheet(t.name);
    sh.getRange(1, 1, 1, t.headers.length).setValues([t.headers]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

function resumeFolder_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('RESUME_FOLDER_ID');
  if (id) {
    try { return DriveApp.getFolderById(id); } catch (ignored) {}
  }
  const folder = DriveApp.createFolder('Fluid Silicon résumés');
  props.setProperty('RESUME_FOLDER_ID', folder.getId());
  return folder;
}

function seenKey_(type, email) {
  return 'seen:' + type + ':' + String(email || '').trim().toLowerCase();
}

function seenRecently_(type, email) {
  return !!CacheService.getScriptCache().get(seenKey_(type, email));
}

function markSeen_(type, email) {
  CacheService.getScriptCache().put(seenKey_(type, email), '1', CONFIG.DUPLICATE_WINDOW_S);
}

function clean_(v, max) {
  if (v === undefined || v === null) return '';
  return String(v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max || 500);
}

/** Text for a sheet cell: never lets a value start a formula. */
function cell_(v, max) {
  const s = clean_(v, max);
  return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
}

function list_(v) {
  return Array.isArray(v) ? v.map(function (x) { return clean_(x, 100); }).join(', ') : clean_(v);
}

function isEmail_(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(clean_(v, 320));
}

function safeName_(s) {
  return s.replace(/[\\/:*?"<>|]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 150);
}

function firstName_(name) {
  return clean_(name).split(/\s+/)[0] || 'there';
}

function days_(n) {
  const words = { 1: 'one business day', 2: 'two business days', 3: 'three business days', 5: 'five business days' };
  return words[n] || (n + ' business days');
}
