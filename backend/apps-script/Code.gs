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
  SHEET_ID: '',                             // fallback: empty means the spreadsheet this script is bound to
  SHEET_IDS: {                              // one spreadsheet per form; empty falls back to SHEET_ID
    demo: '',                               //   ID of the "Demo requests" spreadsheet
    contact: '',                            //   ID of the "Contact messages" spreadsheet
    application: '',                        //   ID of your existing applications spreadsheet
  },
  NOTIFY_DEMO: 'info@fluidsilicon.com, vkogo@fluidsilicon.com, nmavuso@fluidsilicon.com',     // demo requests and contact messages
  NOTIFY_APPLY: 'careers@fluidsilicon.com, vkogo@fluidsilicon.com, nmavuso@fluidsilicon.com', // applications
  SEND_RECEIPTS: true,                      // short confirmation email to the person who submitted
  REPLY_DAYS_DEMO: 2,                       // keep in step with replyDays in config.js
  REPLY_DAYS_APPLY: 5,                      // keep in step with the careers and apply pages
  MAX_RESUME_MB: 5,                         // keep in step with maxResumeMB in config.js
  MIN_ELAPSED_MS: 2500,                     // a form finished faster than this is treated as a bot
  DUPLICATE_WINDOW_S: 120,                  // same email and form inside this window is saved once
  RETENTION_DAYS_DEMO: 0,                   // 0 keeps everything; match the privacy notice before enabling
  RETENTION_DAYS_APPLY: 0,
};

const SIGNATURE = 'Fluid Silicon\nwww.fluidsilicon.com\nPhiladelphia, PA';
const SITE = 'https://fluidsilicon.com';

function esc_(t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

/** The banner image, embedded in each email as an inline attachment so clients show it without a "show images" prompt.
 *  Fetched from the site once per execution and cached for a day; falls back to a remote image if the fetch fails. */
function bannerBlob_() {
  if (bannerBlob_.cache !== undefined) return bannerBlob_.cache;
  try {
    const cache = CacheService.getScriptCache();
    let b64 = cache.get('banner');
    if (!b64) {
      const r = UrlFetchApp.fetch(SITE + '/assets/img/email-banner.png', { muteHttpExceptions: true });
      if (r.getResponseCode() !== 200) throw new Error('banner ' + r.getResponseCode());
      b64 = Utilities.base64Encode(r.getContent());
      cache.put('banner', b64, 21600);
    }
    bannerBlob_.cache = Utilities.newBlob(Utilities.base64Decode(b64), 'image/png', 'email-banner.png');
  } catch (err) {
    console.warn('banner not embedded: ' + err);
    bannerBlob_.cache = null;
  }
  return bannerBlob_.cache;
}

function bannerSrc_() { return bannerBlob_() ? 'cid:banner' : SITE + '/assets/img/email-banner.png'; }

function send_(msg) {
  const blob = bannerBlob_();
  if (blob) msg.inlineImages = { banner: blob };
  MailApp.sendEmail(msg);
}

/** The branded email card: banner, body HTML, signature, footer line. */
function card_(bodyHtml, footer) {
  return '<div style="background:#f6f4ef;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">' +
    '<div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5e1d8">' +
    '<a href="' + SITE + '" style="display:block"><img src="' + bannerSrc_() + '" width="600" height="120" alt="Fluid Silicon" style="display:block;width:100%;height:auto;border:0"></a>' +
    '<div style="padding:28px 36px 32px">' + bodyHtml +
    '<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:28px;border-top:1px solid #e5e1d8;width:100%"><tr>' +
    '<td style="padding-top:18px;font-size:15px;line-height:1.5">' +
    '<span style="font-weight:700;color:#15130f;letter-spacing:.02em">FLUID</span><span style="font-weight:700;color:#a67c00;letter-spacing:.02em">SILICON</span><br>' +
    '<a href="' + SITE + '" style="color:#b04300;text-decoration:none">www.fluidsilicon.com</a><br>' +
    '<span style="color:#6d6860">Philadelphia, PA</span>' +
    '</td></tr></table>' +
    '</div></div>' +
    '<p style="max-width:600px;margin:16px auto 0;font-size:12px;line-height:1.5;color:#6d6860;text-align:center">' + footer + '</p>' +
    '</div>';
}

/** Team notification: a titled card with a field table, the message, and buttons. Sender name is the form's name. */
function notify_(o) {
  const rows = o.fields.filter(function (f) { return f[1]; }).map(function (f) {
    const v = f[2] === 'link' ? '<a href="' + esc_(f[1]) + '" style="color:#b04300">' + esc_(f[1]) + '</a>' : esc_(f[1]);
    return '<tr><td style="padding:7px 16px 7px 0;font-size:13px;color:#6d6860;white-space:nowrap;vertical-align:top">' + esc_(f[0]) + '</td>' +
      '<td style="padding:7px 0;font-size:15px;color:#15130f;vertical-align:top">' + v + '</td></tr>';
  }).join('');
  const msg = o.message ? '<p style="margin:0 0 6px;font-size:13px;color:#6d6860">' + esc_(o.messageLabel || 'Message') + '</p>' +
    '<div style="background:#f6f4ef;border-radius:8px;padding:14px 16px;font-size:15px;line-height:1.55;color:#15130f;white-space:pre-wrap">' + esc_(o.message) + '</div>' : '';
  const btns = (o.buttons || []).filter(function (b) { return b[1]; }).map(function (b, i) {
    const primary = i === 0;
    return '<a href="' + esc_(b[1]) + '" style="display:inline-block;margin:0 10px 10px 0;padding:11px 18px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;' +
      (primary ? 'background:#f06024;color:#121212' : 'background:#ffffff;color:#15130f;border:1px solid #cfc9bc') + '">' + esc_(b[0]) + '</a>';
  }).join('');
  const body =
    '<p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#7d5d00;text-transform:uppercase;letter-spacing:.04em">' + esc_(o.kicker) + '</p>' +
    '<h1 style="margin:0 0 18px;font-size:22px;line-height:1.25;color:#15130f">' + esc_(o.title) + '</h1>' +
    '<table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin-bottom:' + (msg ? '18px' : '6px') + '">' + rows + '</table>' +
    msg + (btns ? '<div style="margin-top:22px">' + btns + '</div>' : '');
  const text = o.title + '\n\n' + o.fields.filter(function (f) { return f[1]; }).map(function (f) { return f[0] + ': ' + f[1]; }).join('\n') +
    (o.message ? '\n\n' + o.message : '') + '\n\n' + (o.buttons || []).filter(function (b) { return b[1]; }).map(function (b) { return b[0] + ': ' + b[1]; }).join('\n');
  send_({ to: o.to, replyTo: o.replyTo, name: o.name, subject: o.subject, body: text,
    htmlBody: card_(body, 'Sent by the fluidsilicon.com forms backend. Reply to this email to answer ' + esc_(o.who) + ' directly.') });
}

/** Receipt email: the same paragraphs as plain text (fallback) and as the branded card. */
function receipt_(to, replyTo, subject, greeting, paragraphs) {
  const text = greeting + '\n\n' + paragraphs.join('\n\n') + '\n\n' + SIGNATURE;
  const ps = paragraphs.map(function (t) { return '<p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:#3f3b33">' + esc_(t) + '</p>'; }).join('');
  const html = card_('<p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:#15130f">' + esc_(greeting) + '</p>' + ps,
    'You are receiving this because you sent a form on fluidsilicon.com. Reply to this email to reach us.');
  send_({ to: to, replyTo: replyTo, name: 'Fluid Silicon', subject: subject, body: text, htmlBody: html });
}

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
  Object.keys(TABS).forEach(function (k) {
    const ss = spreadsheet_(k);
    sheet_(ss, k);
    console.log(TABS[k].name + ': ' + ss.getUrl());
  });
  const folder = resumeFolder_();
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
  purgeTab_(sheet_(spreadsheet_('demo'), 'demo'), CONFIG.RETENTION_DAYS_DEMO, -1);
  purgeTab_(sheet_(spreadsheet_('contact'), 'contact'), CONFIG.RETENTION_DAYS_DEMO, -1);
  purgeTab_(sheet_(spreadsheet_('application'), 'application'), CONFIG.RETENTION_DAYS_APPLY, TABS.application.headers.indexOf('Résumé file ID'));
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
  const sh = sheet_(spreadsheet_('demo'), 'demo');
  sh.appendRow([
    new Date(), cell_(d.name), cell_(d.email), cell_(d.company), cell_(d.title), cell_(list_(d.families)),
    cell_(d.fleetSize), cell_(d.industry), cell_(list_(d.goals)), cell_(d.timeline), cell_(d.message, 5000),
    d.consent ? 'Yes' : 'No', cell_(d.page), 'New', '',
  ]);
}

function saveContact_(d) {
  const sh = sheet_(spreadsheet_('contact'), 'contact');
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
  const sh = sheet_(spreadsheet_('application'), 'application');
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
  notify_({
    to: CONFIG.NOTIFY_DEMO, replyTo: clean_(d.email), name: 'Demo request', who: clean_(d.name),
    subject: 'Demo request: ' + clean_(d.company) + ' (' + clean_(d.name) + ')',
    kicker: 'New demo request', title: clean_(d.company) + ' wants to see the platform',
    fields: [['Name', clean_(d.name)], ['Work email', clean_(d.email)], ['Company', clean_(d.company)], ['Role', clean_(d.title)],
             ['FPGA families', list_(d.families)], ['Fleet size', clean_(d.fleetSize)], ['Industry', clean_(d.industry)],
             ['Priorities', list_(d.goals)], ['Timeline', clean_(d.timeline)]],
    message: clean_(d.message, 5000),
    buttons: [['Reply to ' + firstName_(d.name), 'mailto:' + clean_(d.email)], ['Open demo requests sheet', spreadsheet_('demo').getUrl()]],
  });
  if (CONFIG.SEND_RECEIPTS) {
    receipt_(clean_(d.email), CONFIG.NOTIFY_DEMO.split(',')[0], 'We received your demo request', 'Hi ' + firstName_(d.name) + ',', [
      'Thank you for your interest in trying out the Fluid Silicon platform. We\'re glad you want to see it on real hardware. ' +
        'We received your request and will reply within ' + days_(CONFIG.REPLY_DAYS_DEMO) + ' to set a time for a session.',
      'If it helps, tell us in a reply which devices you run and what you\'d most like to see; we\'ll shape the session around it.',
    ]);
  }
}

function notifyContact_(d) {
  notify_({
    to: CONFIG.NOTIFY_DEMO, replyTo: clean_(d.email), name: 'Contact form', who: clean_(d.name),
    subject: 'Contact (' + clean_(d.topic) + '): ' + (clean_(d.company) || clean_(d.name)),
    kicker: 'New message', title: clean_(d.name) + (clean_(d.company) ? ' at ' + clean_(d.company) : '') + ' wrote in',
    fields: [['Topic', clean_(d.topic)], ['Name', clean_(d.name)], ['Work email', clean_(d.email)], ['Company', clean_(d.company)]],
    message: clean_(d.message, 5000),
    buttons: [['Reply to ' + firstName_(d.name), 'mailto:' + clean_(d.email)], ['Open contact sheet', spreadsheet_('contact').getUrl()]],
  });
  if (CONFIG.SEND_RECEIPTS) {
    receipt_(clean_(d.email), CONFIG.NOTIFY_DEMO.split(',')[0], 'We received your message', 'Hi ' + firstName_(d.name) + ',', [
      'Thanks for writing to Fluid Silicon. We received your message and will reply within ' + days_(CONFIG.REPLY_DAYS_DEMO) + '.',
    ]);
  }
}

function notifyApplication_(d) {
  notify_({
    to: CONFIG.NOTIFY_APPLY, replyTo: clean_(d.email), name: 'Application', who: clean_(d.name),
    subject: 'Application: ' + clean_(d.role) + ' - ' + clean_(d.name),
    kicker: 'New application', title: clean_(d.name) + ' applied for ' + clean_(d.role),
    fields: [['Name', clean_(d.name)], ['Email', clean_(d.email)], ['Phone', clean_(d.phone) === 'Not provided' ? '' : clean_(d.phone)],
             ['Based in', clean_(d.location)], ['Earliest start', clean_(d.startDate)], ['On-site', clean_(d.onsite)],
             ['School', clean_(d.school)], ['Graduation', clean_(d.graduation)], ['LinkedIn', clean_(d.linkedin), 'link'],
             ['Portfolio', clean_(d.portfolio), 'link'], ['Authorized to work in US', clean_(d.workAuthorized)],
             ['Needs sponsorship', clean_(d.needSponsorship)]],
    messageLabel: 'Note from the candidate', message: clean_(d.coverLetter, 10000),
    buttons: [['Open résumé', d._resumeUrl || ''], ['Reply to ' + firstName_(d.name), 'mailto:' + clean_(d.email)], ['All applications', spreadsheet_('application').getUrl()]],
  });
  if (CONFIG.SEND_RECEIPTS) {
    receipt_(clean_(d.email), CONFIG.NOTIFY_APPLY.split(',')[0], 'We received your application', 'Hi ' + firstName_(d.name) + ',', [
      'Thank you for applying for ' + clean_(d.role) + ' at Fluid Silicon. The team will look at your application and get back to you within ' +
        days_(CONFIG.REPLY_DAYS_APPLY) + '.',
    ]);
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

function spreadsheet_(key) {
  const id = (key && CONFIG.SHEET_IDS && CONFIG.SHEET_IDS[key]) || CONFIG.SHEET_ID;
  return id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
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
