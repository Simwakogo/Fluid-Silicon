# Website forms backend (Google Apps Script)

`Code.gs` receives both website forms, demo requests and job applications, and:

- writes each one to a Google Sheet ("Demo requests" and "Applications" tabs),
- saves résumés to a private Drive folder and links them from the sheet,
- emails the team (reply-to is the person who submitted) and sends them a short receipt,
- drops bots quietly (honeypot field and a minimum time on the form),
- saves a double-click once, and refuses bad input with a message the site shows,
- can delete old submissions on a schedule to match the privacy notice.

## Where things stand today

| Form | Posts to | What happens |
|---|---|---|
| Apply | The Apps Script URL your current site already uses (`applyEndpoint` in `config.js`) | Works now. Your existing script saves the fields it already knew. Location, start date, on-site, school and links are only saved once you switch to `Code.gs`. |
| Request a demo | `demoEndpoint`, empty for now | The form checks the fields, then shows your email address with a "Copy my details" button and an email link. Nothing fails silently. |

Phone is optional now, and the visa-type and visa-expiry fields are gone: the form asks only the two standard work-authorization questions. So that a script expecting the old fields keeps accepting applications, the site sends `phone: "Not provided"` when it's left blank, and `visaType` / `visaExpiration` as `"Not asked"` when someone needs sponsorship. The new script stores these values as they arrive.

## Three separate spreadsheets

By default all three forms write to tabs of the spreadsheet the script is bound to. To keep them in separate files, put each file's ID in `CONFIG.SHEET_IDS` (the ID is the long string in the sheet's URL between `/d/` and `/edit`). For applications, use your existing applications spreadsheet: the script adds a tab named "Applications" with the full set of columns (location, start date, on-site, school, links and so on) and writes new applications there, leaving your existing tab untouched. Each form notifies its own address (`NOTIFY_DEMO` for demo requests and contact messages, `NOTIFY_APPLY` for applications).

## Deploy

1. Create a Google Sheet in the Workspace account that should own submissions.
2. Open **Extensions > Apps Script**. Replace the default file with `Code.gs`. In Project Settings, show `appsscript.json` and replace it with the one here (time zone and web-app access).
3. Edit `CONFIG` at the top of `Code.gs`: notification addresses, reply times, retention.
4. Run `setup()` once from the editor and approve the permissions. The log prints the sheet and résumé-folder links. Share the résumé folder with the hiring team only.
5. **Deploy > New deployment > Web app**. Execute as: *Me*. Who has access: *Anyone*. Copy the `/exec` URL.
6. In `src/assets/js/config.js` set `demoEndpoint` and `applyEndpoint` to that URL. Rebuild and publish.
7. Send one test of each form from the live site. Check the sheet, the folder and both emails.

When you change `Code.gs` later, use **Deploy > Manage deployments > Edit > Version: New version**. That keeps the same URL. A brand-new deployment gets a new URL, and `config.js` would have to change too.

## Retention

`RETENTION_DAYS_DEMO` and `RETENTION_DAYS_APPLY` default to `0`, which keeps everything. Set them to the periods in your privacy notice, then run `installRetentionTrigger()` once. A daily job deletes older rows and moves their résumés to the Drive trash.

## Test without deploying

```
node backend/apps-script/test/run-tests.js
```

The tests stand in for Sheets, Drive, Mail, Cache and Lock. They cover valid demo and application posts, the old site's payload, bots, bad input, oversized or wrong-type résumés, double submits, retrying after a failed save, formula injection in cells, and the retention purge.

## Request format

`POST` with a JSON body and no `Content-Type` header, so the browser sends it without a CORS preflight. Reply: `{"status":"ok"}` or `{"status":"error","message":"…"}`.

Demo request fields: `formType: "demo"`, `name`, `email`, `company`, `title`, `families[]`, `fleetSize`, `industry`, `goals[]`, `timeline`, `message`, `consent`, `website` (honeypot), `elapsedMs`, `page`.

Application fields: `formType: "application"`, `name`, `email`, `phone`, `location`, `role`, `startDate`, `onsite`, `school`, `graduation`, `linkedin`, `portfolio`, `coverLetter`, `workAuthorized`, `needSponsorship`, `honeypot`, `elapsedMs`, `fileName`, `mimeType`, `fileData` (base64). `visaType` and `visaExpiration` are still sent as empty strings for the old script.
