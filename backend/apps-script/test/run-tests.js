// Offline tests for Code.gs. Mocks the Apps Script services it uses and runs doPost()
// against the payloads the website sends.   node backend/apps-script/test/run-tests.js
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

function makeEnv(opts) {
  opts = opts || {};
  const sheets = {};
  const mail = [];
  const files = {};
  const cache = {};
  const props = {};
  let fileN = 0;
  function Sheet(name) {
    this.name = name; this.rows = [];
    this.getRange = (r, c, nr, nc) => ({
      setValues: (v) => { this.rows[r - 1] = v[0].slice(); return { setFontWeight: () => {} }; },
    });
    this.setFrozenRows = () => {};
    this.appendRow = (row) => { if (opts.failAppend && opts.failAppend()) throw new Error('quota'); this.rows.push(row.slice()); };
    this.getDataRange = () => ({ getValues: () => this.rows.map(r => r.slice()) });
    this.deleteRow = (n) => { this.rows.splice(n - 1, 1); };
  }
  const ss = {
    getSheetByName: (n) => sheets[n] || null,
    insertSheet: (n) => (sheets[n] = new Sheet(n)),
    getUrl: () => 'https://docs.google.com/spreadsheets/d/TEST',
  };
  const folder = {
    createFile: (blob) => { const id = 'f' + (++fileN); files[id] = { blob, trashed: false }; return { getUrl: () => 'https://drive.google.com/file/d/' + id, getId: () => id }; },
    getUrl: () => 'https://drive.google.com/drive/folders/RES',
    getId: () => 'RES',
  };
  const ctx = {
    console: { log() {}, error() {} },
    SpreadsheetApp: { getActiveSpreadsheet: () => ss, openById: () => ss },
    DriveApp: {
      createFolder: () => folder,
      getFolderById: (id) => { if (id !== 'RES') throw new Error('no folder'); return folder; },
      getFileById: (id) => ({ setTrashed: (t) => { files[id].trashed = t; } }),
    },
    MailApp: { sendEmail: (m) => mail.push(m) },
    UrlFetchApp: { fetch: () => ({ getResponseCode: () => 200, getContent: () => Buffer.from('png') }) },
    console: { log() {}, warn() {}, error() {} },
    Utilities: {
      newBlob: (bytes, type, name) => ({ bytes, type, name }),
      base64Encode: (b) => Buffer.from(b).toString('base64'),
      base64Decode: (s) => Buffer.from(s, 'base64'),
      formatDate: (d) => d.toISOString().slice(0, 10),
    },
    ContentService: {
      MimeType: { JSON: 'json' },
      createTextOutput: (s) => ({ text: s, setMimeType() { return this; } }),
    },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    CacheService: { getScriptCache: () => ({ get: (k) => cache[k] || null, put: (k, v) => { cache[k] = v; } }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props[k] || null, setProperty: (k, v) => { props[k] = v; } }) },
    ScriptApp: { getProjectTriggers: () => [], deleteTrigger() {}, newTrigger: () => ({ timeBased: () => ({ everyDays: () => ({ atHour: () => ({ create() {} }) }) }) }) },
    Date, JSON, Math, String, Array, Object, Buffer,
  };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8'), ctx);
  return { ctx, sheets, mail, files, cache };
}

function post(env, body) {
  const out = env.ctx.doPost({ postData: { contents: typeof body === 'string' ? body : JSON.stringify(body) } });
  return JSON.parse(out.text);
}

const demo = {
  formType: 'demo', name: 'Ada Lovelace', email: 'ada@example.com', company: 'Analytical Engines', title: 'Reliability lead',
  families: ['AMD UltraScale+', 'Altera Agilex'], fleetSize: '1,000 to 10,000', industry: 'Data center and hyperscale',
  goals: ['Energy efficiency'], timeline: 'Evaluating this quarter', message: 'Hello', consent: true, website: '',
  elapsedMs: 42000, page: 'https://fluidsilicon.com/demo/',
};
const pdf = Buffer.from('%PDF-1.4 test résumé').toString('base64');
const application = {
  formType: 'application', name: 'Grace Hopper', email: 'grace@example.com', phone: '+1 215 555 0100', location: 'Philadelphia, PA',
  role: 'FPGA Engineer', startDate: '2026-11-02', onsite: 'Yes, I live nearby', school: '', graduation: '', linkedin: '', portfolio: '',
  coverLetter: 'Note', workAuthorized: 'Yes', needSponsorship: 'No', visaType: '', visaExpiration: '', honeypot: '', elapsedMs: 90000,
  fileName: 'grace.pdf', mimeType: 'application/pdf', fileData: pdf,
};
const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('demo request is saved and both emails go out', () => {
  const env = makeEnv();
  assert.deepStrictEqual(post(env, demo), { status: 'ok' });
  const rows = env.sheets['Demo requests'].rows;
  assert.strictEqual(rows.length, 2);
  assert.strictEqual(rows[1][1], 'Ada Lovelace');
  assert.strictEqual(rows[1][5], 'AMD UltraScale+, Altera Agilex');
  assert.strictEqual(env.mail.length, 2);
  assert.strictEqual(env.mail[0].to, 'info@fluidsilicon.com, vkogo@fluidsilicon.com, nmavuso@fluidsilicon.com');
  assert.strictEqual(env.mail[0].replyTo, 'ada@example.com');
  assert.ok(/two business days/.test(env.mail[1].body));
});

test('contact message is saved and both emails go out', () => {
  const env = makeEnv();
  const msg = { formType: 'contact', name: 'Ada Lovelace', email: 'ada@example.com', company: 'Analytical Engines', topic: 'Partnership',
    message: 'We build accelerator cards and would like to talk.', consent: true, elapsedMs: 30000, page: 'https://fluidsilicon.com/contact/' };
  assert.deepStrictEqual(post(env, msg), { status: 'ok' });
  const rows = env.sheets['Contact messages'].rows;
  assert.strictEqual(rows.length, 2);
  assert.strictEqual(rows[1][4], 'Partnership');
  assert.strictEqual(env.mail.length, 2);
  assert.ok(/Contact \(Partnership\)/.test(env.mail[0].subject));
  assert.strictEqual(post(env, Object.assign({}, msg, { message: '' })).status, 'error');
});

test('application is saved with the résumé in Drive', () => {
  const env = makeEnv();
  assert.deepStrictEqual(post(env, application), { status: 'ok' });
  const rows = env.sheets['Applications'].rows;
  assert.strictEqual(rows.length, 2);
  assert.strictEqual(rows[1][5], 'FPGA Engineer');
  assert.ok(/drive\.google\.com\/file\/d\/f1/.test(rows[1][15]));
  const f = env.files.f1.blob;
  assert.strictEqual(f.type, 'application/pdf');
  assert.ok(/Grace Hopper - FPGA Engineer\.pdf$/.test(f.name));
  assert.strictEqual(Buffer.from(f.bytes).toString(), '%PDF-1.4 test résumé');
  assert.strictEqual(env.mail[0].to, 'careers@fluidsilicon.com, vkogo@fluidsilicon.com, nmavuso@fluidsilicon.com');
});

test('the original site payload (no formType) still works', () => {
  const env = makeEnv();
  const legacy = Object.assign({}, application);
  delete legacy.formType; delete legacy.elapsedMs;
  assert.strictEqual(post(env, legacy).status, 'ok');
  assert.strictEqual(env.sheets['Applications'].rows.length, 2);
});

test('honeypot and too-fast submissions are accepted quietly and not stored', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, Object.assign({}, demo, { website: 'spam' })).status, 'ok');
  assert.strictEqual(post(env, Object.assign({}, application, { honeypot: 'x' })).status, 'ok');
  assert.strictEqual(post(env, Object.assign({}, demo, { elapsedMs: 300 })).status, 'ok');
  assert.ok(!env.sheets['Demo requests'] && !env.sheets['Applications']);
  assert.strictEqual(env.mail.length, 0);
});

test('invalid input is refused with a message', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, Object.assign({}, demo, { email: 'nope' })).status, 'error');
  assert.strictEqual(post(env, Object.assign({}, demo, { consent: false })).status, 'error');
  assert.strictEqual(post(env, Object.assign({}, application, { fileName: 'cv.exe' })).status, 'error');
  const big = Buffer.alloc(6 * 1024 * 1024).toString('base64');
  const r = post(env, Object.assign({}, application, { fileData: big }));
  assert.strictEqual(r.status, 'error'); assert.ok(/5 MB/.test(r.message));
  assert.strictEqual(post(env, '{not json').status, 'error');
  assert.strictEqual(post(env, Object.assign({}, demo, { formType: 'other' })).status, 'error');
});

test('a double submit is saved once', () => {
  const env = makeEnv();
  post(env, demo); post(env, demo);
  assert.strictEqual(env.sheets['Demo requests'].rows.length, 2);
});

test('a failed save can be retried straight away', () => {
  let fail = true;
  const env = makeEnv({ failAppend: () => fail });
  assert.strictEqual(post(env, demo).status, 'error');
  fail = false;
  assert.strictEqual(post(env, demo).status, 'ok');
  assert.strictEqual(env.sheets['Demo requests'].rows.length, 2);
});

test('cell values cannot start a formula', () => {
  const env = makeEnv();
  post(env, Object.assign({}, demo, { company: '=HYPERLINK("http://x","y")' }));
  assert.strictEqual(env.sheets['Demo requests'].rows[1][3], "'=HYPERLINK(\"http://x\",\"y\")");
});

test('retention purge removes old rows and trashes their résumés', () => {
  const env = makeEnv();
  post(env, application);
  const rows = env.sheets['Applications'].rows;
  rows[1][0] = new Date(Date.now() - 400 * 86400000);
  vm.runInContext('CONFIG.RETENTION_DAYS_APPLY = 365', env.ctx);
  env.ctx.purgeOldSubmissions();
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(env.files.f1.trashed, true);
});

let failed = 0;
for (const [name, fn] of tests) {
  try { fn(); console.log('  ok  ' + name); } catch (e) { failed++; console.log('FAIL  ' + name + '\n      ' + e.message); }
}
console.log(failed ? failed + ' failed' : 'all ' + tests.length + ' passed');
process.exit(failed ? 1 : 0);
