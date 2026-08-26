// ============================================================
// FLUID SILICON SITE CONTENT
// Edit this file to change the site. No HTML knowledge needed.
// ============================================================

window.SITE = {

  // Home page video. Set to "assets/video/home.mp4" when the video is ready.
  // While null, the animated chip fabric shows instead.
  video: null,

  // ---- Solution pillars (home page). One sentence each. ----
  solutions: [
    { title: "Silicon Health Monitoring",
      text: "On-chip sensors measure the health of logic at speed of operation, on unmodified commercial devices." },
    { title: "Adaptive Compensation",
      text: "Chip operation is automatically tuned to the real, measured characteristics of each individual device rather than a fixed worst-case average." },
    { title: "Self-Healing",
      text: "Degrading resources detected, isolated, and repaired on the fly, before they fail." }
  ],

  // ---- How it works (home page). A real sequence. ----
  steps: [
    { n: "01", title: "Sense",
      text: "Built-in sensors continuously measure timing health across the device, without requiring any additional hardware." },
    { n: "02", title: "Track",
      text: "The platform follows each device over its lifetime and anticipates failures before they happen." },
    { n: "03", title: "Act",
      text: "Tuning and repair happen through reconfiguration, without interrupting the system's ongoing operation." }
  ],

  // ---- Industries (home band + industries page). One sentence each. ----
  industries: [
    { name: "Aerospace & Defense",
      tag: "Reliability · Lifetime",
      text: "Health monitoring and in-field repair for missions where replacement is impossible.",
      detail: "Once a system is deployed, whether on a satellite, an aircraft, or in a remote installation, physically replacing a chip is rarely an option. Fluid Silicon gives these systems the ability to monitor their own condition over the full length of a mission and repair themselves in place, extending the usable life of hardware that has to keep working long after it's out of reach." },
    { name: "Hyperscale & Cloud",
      tag: "Energy · Reliability",
      text: "Health monitoring and adaptive tuning to cut energy across the fleet.",
      detail: "Hyperscale operators run enormous fleets of chips built to the same conservative, worst-case spec, even though every individual device performs a little differently once deployed. Fluid Silicon lets each device in the fleet be tuned to its own real capability rather than a fixed average, translating into meaningful energy savings at the scale data centers operate." },
    { name: "Telecom & High-Reliability",
      tag: "Reliability · Performance",
      text: "Continuous monitoring, compensation, and repair for systems that cannot fail quietly.",
      detail: "Telecom infrastructure, from cell towers to core network equipment, has to stay reliable for years with minimal physical access. Fluid Silicon continuously tracks the health of the chips running that infrastructure, compensates for how they age and drift over time, and repairs degrading components before they cause an outage." },
    { name: "Finance & HFT",
      tag: "Latency",
      text: "Performance tuned to the measured limits of each chip for lower, verified latency.",
      detail: "In low-latency trading, microseconds determine outcomes, and chips are typically run conservatively to guarantee stability. Fluid Silicon measures the real, individual limits of each chip and tunes performance to match, giving trading infrastructure verified, repeatable latency gains without sacrificing the reliability the business depends on." }
  ],

  // ---- Careers listings. href points to the job page. ----
  jobs: {
    fulltime: [
      { title: "FPGA Engineer",
        meta: "Full-Time · Philadelphia",
        href: "jobs/fpga-engineer.html" },
      { title: "Systems Software Engineer, HW/SW Co-Design",
        meta: "Full-Time · Philadelphia",
        href: "jobs/systems-software-engineer.html" }
    ],
    intern: [
      { title: "Software Engineering Intern",
        meta: "Internship · Philadelphia",
        href: "jobs/internships.html#swe" },
      { title: "Hardware Design / FPGA Intern",
        meta: "Internship · Philadelphia",
        href: "jobs/internships.html#hde" },
      { title: "Business Development Intern",
        meta: "Internship · Philadelphia",
        href: "jobs/internships.html#bd" }
    ]
  },

  // ---- Recognition (home page). Add items to add logos. ----
  recognition: [
    { img: "assets/img/presidents_sustainability_prize.png",
      caption: "President's Sustainability Prize · University of Pennsylvania" }
  ]
};
