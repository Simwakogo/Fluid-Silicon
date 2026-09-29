/* Fluid Silicon site settings. Edit these values and publish again; the file is copied as-is, so no page needs to change.
   demoEndpoint   Google Apps Script web-app URL that receives demo requests (see backend/apps-script/README.md).
                  Leave empty and the demo form shows your email address and a copy button instead of failing silently.
   applyEndpoint  Web-app URL that receives job applications. This is the endpoint your current site already uses;
                  point it at the new script's URL once deployed so the extra fields (location, links, school) are saved.
   calendarUrl    Optional booking link (for example a Cal.com or Calendly page), offered after a demo request.
   replyDays      Business days you commit to for replying to demo requests. */
window.FS_CONFIG = {
  demoEndpoint: "https://script.google.com/macros/s/AKfycbw_SsF_xRy6cN6pB3E6vckk-hrAQ5wve5dwBSBFtDwSdAN-RpVXnf2PicufTfXxU_i63g/exec",
  applyEndpoint: "https://script.google.com/macros/s/AKfycbw_SsF_xRy6cN6pB3E6vckk-hrAQ5wve5dwBSBFtDwSdAN-RpVXnf2PicufTfXxU_i63g/exec",
  calendarUrl: "",
  replyDays: 2,
  contactEmail: "info@fluidsilicon.com",
  careersEmail: "careers@fluidsilicon.com",
  maxResumeMB: 5
};
