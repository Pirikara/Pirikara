(() => {
  "use strict";

  const output = document.getElementById("terminal-output");
  const screen = document.getElementById("terminal-screen");
  const form = document.getElementById("terminal-form");
  const input = document.getElementById("terminal-input");
  const pathLabel = document.querySelector(".prompt-path");
  const year = document.getElementById("year");
  year.textContent = String(new Date().getFullYear());

  const advisories = [
    { key: "rack", name: "Rack", id: "CVE-2025-61919", detail: "Unbounded URL-encoded body parsing can exhaust memory.", url: "https://github.com/advisories/GHSA-6xw4-3v39-52mm" },
    { key: "rails", name: "Rails Active Storage", id: "CVE-2026-33174", detail: "Large Range requests in proxy mode can cause a denial of service.", url: "https://github.com/advisories/GHSA-r46p-8f7g-vvvg" },
    { key: "puma", name: "Puma", id: "CVE-2026-47736", detail: "The PROXY Protocol v1 parser can exhaust server memory.", url: "https://github.com/advisories/GHSA-qpgp-93vx-g8v8" },
    { key: "nextcloud", name: "Nextcloud", id: "CVE-2026-45157", detail: "A valid share token can expose temporary upload files.", url: "https://github.com/nextcloud/security-advisories/security/advisories/GHSA-45pj-p7x7-4mhc" }
  ];
  const projects = [
    { key: "vuln-chaser-core", name: "vuln-chaser-core", detail: "IAST + LLM proof of concept for analyzing runtime traces.", url: "https://github.com/Pirikara/vuln-chaser-core" },
    { key: "caseforge", name: "caseforge", detail: "Generates and runs API test scenarios from OpenAPI specifications.", url: "https://github.com/Pirikara/caseforge" }
  ];
  const externalLinks = {
    github: { name: "GitHub", url: "https://github.com/Pirikara" },
    hackerone: { name: "HackerOne", url: "https://hackerone.com/pirikara" },
    qiita: { name: "Qiita", url: "https://qiita.com/gakinchoy7" },
    x: { name: "X", url: "https://x.com/Piri_kara" },
    stackoverflow: { name: "Stack Overflow", url: "https://stackoverflow.com/users/13829308/pirikara" }
  };
  const help = [
    ["whoami", "A quick introduction"],
    ["about", "What I work on"],
    ["disclosures", "Public vulnerability reports"],
    ["projects", "Selected open source projects"],
    ["links", "Find me elsewhere"],
    ["ls / cd / cat", "Explore the virtual file system"],
    ["open <name>", "Open a project or profile"],
    ["clear", "Clear the terminal"]
  ];
  const commandNames = ["help", "whoami", "about", "disclosures", "projects", "links", "ls", "cd", "cat", "pwd", "open", "clear", "date", "echo", "banner"];
  const directories = ["disclosures", "projects", "links"];
  const history = [];
  let historyIndex = 0;
  let historyDraft = "";
  let cwd = "~";

  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };

  const addLine = (parent, text, className = "") => {
    const line = node("p", className, text);
    parent.append(line);
    return line;
  };

  const addLink = (parent, label, url) => {
    const link = node("a", "", label);
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    parent.append(link);
    return link;
  };

  const addHeading = (parent, text) => parent.append(node("span", "response-heading", text));

  const addResult = (parent, name, detail, url) => {
    const row = node("p", "result-row");
    const title = node("strong");
    if (url) addLink(title, name, url);
    else title.textContent = name;
    row.append(title, node("span", "", detail));
    parent.append(row);
  };

  const makeEntry = (command) => {
    const entry = node("div", "terminal-entry");
    const commandLine = node("p", "terminal-command");
    commandLine.append(node("span", "prompt", `pirikara@portfolio:${cwd}$`), document.createTextNode(command));
    const response = node("div", "terminal-response");
    entry.append(commandLine, response);
    output.append(entry);
    return response;
  };

  const scrollToLatest = () => { output.scrollTop = output.scrollHeight; };
  const setCwd = (next) => {
    cwd = next;
    pathLabel.textContent = next === "~" ? "~" : `~/${next}`;
  };

  const showHelp = (parent) => {
    addHeading(parent, "AVAILABLE COMMANDS");
    for (const [command, description] of help) {
      const row = node("p", "help-row");
      row.append(node("code", "", command), node("span", "", description));
      parent.append(row);
    }
    addLine(parent, "Tip: ↑↓ for history, Tab to complete, Ctrl+L to clear.", "muted");
  };

  const showWhoami = (parent) => {
    addHeading(parent, "Tomoya Yamashita  /  Pirikara");
    addLine(parent, "Security Engineer · Bug Bounty Hunter · Japan");
    addLine(parent, "I investigate vulnerabilities in web applications and open source software, build tools, and disclose findings responsibly.");
  };

  const showAbout = (parent) => {
    addHeading(parent, "ABOUT / 研究分野");
    addLine(parent, "I look for the behavior a system didn't expect: in parsers, file handling, access boundaries, and the code paths between them.");
    addLine(parent, "My public work includes vulnerability reports and experiments in security testing.");
    addLine(parent, "Web アプリケーションと OSS の脆弱性調査に取り組んでいます。", "muted");
  };

  const showDisclosures = (parent) => {
    addHeading(parent, "PUBLIC DISCLOSURES / REPORTER CREDIT");
    for (const item of advisories) addResult(parent, item.name, item.id, item.url);
    addLine(parent, "Try: cat disclosures/rack.md", "muted");
  };

  const showProjects = (parent) => {
    addHeading(parent, "SELECTED PROJECTS");
    for (const item of projects) addResult(parent, item.name, item.detail, item.url);
    addLine(parent, "Try: cat projects/caseforge.md", "muted");
  };

  const showLinks = (parent) => {
    addHeading(parent, "FIND ME ELSEWHERE");
    for (const [key, item] of Object.entries(externalLinks)) addResult(parent, item.name, item.url, item.url);
    addLine(parent, "Try: open github", "muted");
  };

  const showListing = (parent, requested) => {
    const path = requested.replace(/\/$/, "").replace(/^~\//, "").replace(/^\.\//, "");
    const directory = !path || path === "." ? cwd : path === "~" || path === ".." ? "~" : path;
    if (directory !== "~" && !directories.includes(directory)) {
      addLine(parent, `ls: ${requested}: No such directory`, "error");
      return;
    }
    addHeading(parent, directory === "~" ? "/home/pirikara" : `/home/pirikara/${directory}`);
    const names = directory === "~"
      ? ["about.txt", "disclosures/", "projects/", "links/"]
      : directory === "disclosures" ? advisories.map((item) => `${item.key}.md`)
      : directory === "projects" ? projects.map((item) => `${item.key}.md`)
      : Object.keys(externalLinks).map((key) => `${key}.url`);
    for (const name of names) addLine(parent, name, name.endsWith("/") ? "directory" : "");
  };

  const showFile = (parent, requested) => {
    const path = requested.replace(/^~\//, "").replace(/^\.\//, "");
    const resolved = path.includes("/") ? path : cwd === "~" ? path : `${cwd}/${path}`;
    if (resolved === "about.txt") return showAbout(parent);
    if (resolved === "README.md") return showHelp(parent);
    const [folder, file] = resolved.split("/");
    if (folder === "disclosures") {
      const item = advisories.find((entry) => `${entry.key}.md` === file);
      if (item) {
        addHeading(parent, `${item.name} / ${item.id}`);
        addLine(parent, item.detail);
        addLink(parent, "Read the advisory ↗", item.url);
        return;
      }
    }
    if (folder === "projects") {
      const item = projects.find((entry) => `${entry.key}.md` === file);
      if (item) {
        addHeading(parent, item.name);
        addLine(parent, item.detail);
        addLink(parent, "View the repository ↗", item.url);
        return;
      }
    }
    if (folder === "links") {
      const key = file?.replace(/\.url$/, "");
      if (key && `${key}.url` === file && externalLinks[key]) {
        addLink(parent, externalLinks[key].url, externalLinks[key].url);
        return;
      }
    }
    addLine(parent, `cat: ${requested}: No such file`, "error");
  };

  const changeDirectory = (parent, requested) => {
    const path = (requested || "~").replace(/\/$/, "");
    if (path === "~" || path === "/home/pirikara" || path === "../" || path === "..") return setCwd("~");
    const target = path.replace(/^~\//, "").replace(/^\.\//, "");
    if (directories.includes(target)) return setCwd(target);
    addLine(parent, `cd: ${requested}: No such directory`, "error");
  };

  const openDestination = (parent, requested) => {
    const key = requested.toLowerCase();
    const target = externalLinks[key]
      || projects.find((item) => item.key === key)
      || advisories.find((item) => item.key === key || item.id.toLowerCase() === key);
    if (!target) {
      addLine(parent, "Usage: open github | hackerone | qiita | x | stackoverflow | caseforge | vuln-chaser-core | rack | rails | puma | nextcloud", "error");
      return;
    }
    window.open(target.url, "_blank", "noopener,noreferrer");
    addLine(parent, `Opening ${target.name} ↗`);
    addLink(parent, target.url, target.url);
  };

  const execute = (raw, options = {}) => {
    const command = raw.trim();
    if (!command) return;
    if (options.remember !== false) {
      history.push(command);
      historyIndex = history.length;
      historyDraft = "";
    }
    const response = makeEntry(command);
    const [verbRaw, ...parts] = command.split(/\s+/);
    const verb = verbRaw.toLowerCase();
    const arg = parts.join(" ");

    switch (verb) {
      case "help": showHelp(response); break;
      case "whoami": showWhoami(response); break;
      case "about": showAbout(response); break;
      case "disclosures": showDisclosures(response); break;
      case "projects": showProjects(response); break;
      case "links": showLinks(response); break;
      case "ls": showListing(response, arg); break;
      case "pwd": addLine(response, cwd === "~" ? "/home/pirikara" : `/home/pirikara/${cwd}`); break;
      case "cd": changeDirectory(response, arg); break;
      case "cat": arg ? showFile(response, arg) : addLine(response, "Usage: cat <file>  ·  Try: cat about.txt", "error"); break;
      case "open": openDestination(response, arg); break;
      case "date": addLine(response, new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Tokyo", dateStyle: "full", timeStyle: "medium" }).format(new Date()) + " JST"); break;
      case "echo": addLine(response, arg); break;
      case "banner": addLine(response, "PIRIKARA // SECURITY RESEARCH // JAPAN"); break;
      case "clear": output.replaceChildren(); break;
      default: addLine(response, `Command not found: ${verb}. Type help for available commands.`, "error");
    }
    input.value = "";
    scrollToLatest();
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    execute(input.value);
    input.focus();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!history.length) return;
      if (historyIndex === history.length) historyDraft = input.value;
      historyIndex = Math.max(0, historyIndex - 1);
      input.value = history[historyIndex];
      input.setSelectionRange(input.value.length, input.value.length);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!history.length) return;
      historyIndex = Math.min(history.length, historyIndex + 1);
      input.value = historyIndex === history.length ? historyDraft : history[historyIndex];
      input.setSelectionRange(input.value.length, input.value.length);
    } else if (event.key === "Tab") {
      const partial = input.value.trimStart();
      const candidates = partial.includes(" ")
        ? partial.startsWith("open ") ? Object.keys(externalLinks).concat(projects.map((item) => item.key), advisories.map((item) => item.key)).map((name) => `open ${name}`)
        : partial.startsWith("cd ") ? directories.map((name) => `cd ${name}`)
        : partial.startsWith("cat ") ? ["cat about.txt", ...advisories.map((item) => `cat disclosures/${item.key}.md`), ...projects.map((item) => `cat projects/${item.key}.md`)]
        : []
        : commandNames;
      const matches = candidates.filter((name) => name.startsWith(partial.toLowerCase()));
      if (matches.length) {
        event.preventDefault();
        if (matches.length === 1) input.value = matches[0] + " ";
        else {
          const entry = makeEntry(partial || "tab");
          addLine(entry, matches.join("    "), "muted");
          scrollToLatest();
        }
      }
    } else if (event.key.toLowerCase() === "l" && event.ctrlKey) {
      event.preventDefault();
      output.replaceChildren();
    }
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-command]");
    if (!button) return;
    execute(button.dataset.command);
    screen.scrollIntoView({ behavior: "smooth", block: "center" });
    input.focus({ preventScroll: true });
  });

  document.getElementById("terminal-window").addEventListener("click", (event) => {
    if (!event.target.closest("a, button, input")) input.focus();
  });
})();
