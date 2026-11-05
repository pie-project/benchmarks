window.Pie = window.Pie || {};

// Log in: a sheet over the page, as macOS slides one down from a window's toolbar, with Google, Microsoft and an
// emailed link, kept by Supabase Auth (config/auth.js). Signed in, the button shows the account and opens a small
// sheet to log out; the sections only an account opens (Measurements, Catalog, Resources) show in the sidebar.
(() => {
  const { url, anonKey } = Pie.authConfig || {};
  const configured = Boolean(url && anonKey);
  const SDK = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";
  const esc = (text) => Pie.format.escape(text);
  const button = document.getElementById("toolbar-login");
  let client = null;
  let user = null;

  // the session Supabase keeps in this browser, read at once so a reload of a signed-in page stays on it while the
  // client starts; the client then confirms it or clears it
  try {
    const ref = configured ? new URL(url).hostname.split(".")[0] : "";
    const kept = ref && JSON.parse(localStorage.getItem(`sb-${ref}-auth-token`) || "null");
    if (kept?.user && kept.expires_at * 1000 > Date.now()) user = kept.user;
  } catch { /* no session kept */ }

  const changed = () => {
    button.textContent = user ? (user.user_metadata?.full_name || user.email || "Account") : "Log in";
    button.classList.toggle("is-signed-in", Boolean(user));
    document.dispatchEvent(new CustomEvent("pie:account"));
  };

  const start = () => new Promise((resolve, reject) => {
    if (client) return resolve(client);
    const script = document.createElement("script");
    script.src = SDK;
    script.onload = () => {
      // the address's session is read here, not by the client: the site rewrites its address as it draws its first page
      client = window.supabase.createClient(url, anonKey, { auth: { detectSessionInUrl: false } });
      client.auth.onAuthStateChange((_event, session) => {
        const was = user?.id;
        user = session?.user || null;
        if (was !== user?.id) changed();
      });
      resolve(client);
    };
    script.onerror = () => reject(new Error("Could not load Supabase"));
    document.head.append(script);
  });
  // a visit back from a provider or an emailed link carries its session in the address: read at once, before the site
  // rewrites the address for its own pages, then handed to the client, and the address cleaned of it
  const returned = (() => {
    const hash = new URLSearchParams(location.hash.slice(1)), query = new URLSearchParams(location.search);
    return { access: hash.get("access_token"), refresh: hash.get("refresh_token"), code: query.get("code"),
      error: hash.get("error_description") || query.get("error_description") };
  })();
  let arrival = null;  // what came back, for the sheet to say when it was an error
  if (returned.access || returned.code || returned.error) {
    history.replaceState(null, "", location.pathname);
    if (returned.error) arrival = returned.error.replace(/\+/g, " ");
  }
  if (configured && (returned.access || returned.code)) {
    start().then(async (c) => {
      const { error } = returned.access
        ? await c.auth.setSession({ access_token: returned.access, refresh_token: returned.refresh })
        : await c.auth.exchangeCodeForSession(returned.code);
      if (error) { arrival = error.message; return; }
      const { data } = await c.auth.getUser();
      user = data?.user || null;
      changed();
    }).catch((error) => { arrival = error.message; });
  } else if (configured && user) {
    start().catch(() => {});
  }

  // the sheet
  const back = document.createElement("div");
  back.className = "account-backdrop";
  back.hidden = true;
  document.body.append(back);
  const close = () => { back.hidden = true; back.innerHTML = ""; button.setAttribute("aria-expanded", "false"); };
  const GOOGLE = '<svg viewBox="0 0 18 18" aria-hidden="true"><path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"/><path fill="#FBBC05" d="M3.97 10.72A5.4 5.4 0 0 1 3.68 9c0-.6.1-1.18.29-1.72V4.95H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.05l3.01-2.33z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/></svg>';
  const MICROSOFT = '<svg viewBox="0 0 18 18" aria-hidden="true"><path fill="#F25022" d="M1 1h7.5v7.5H1z"/><path fill="#7FBA00" d="M9.5 1H17v7.5H9.5z"/><path fill="#00A4EF" d="M1 9.5h7.5V17H1z"/><path fill="#FFB900" d="M9.5 9.5H17V17H9.5z"/></svg>';
  const note = (text, kind = "") => { const n = back.querySelector(".account-note"); if (n) { n.textContent = text; n.className = `account-note ${kind}`; n.hidden = !text; } };
  const here = () => location.origin + location.pathname;
  // which logins the project has on (Google, Microsoft), asked of it once: a click on one that is off says so in the
  // sheet, so none leads to Supabase's bare "provider is not enabled" page
  let providers = null;
  const enabled = () => providers ||= configured
    ? fetch(`${url}/auth/v1/settings`, { headers: { apikey: anonKey } }).then((r) => r.json()).then((d) => d.external || {}).catch(() => ({}))
    : Promise.resolve({});
  // Supabase's messages, said as the site would
  const plain = (message) => /signups? not allowed/i.test(message) ? "This email has no account here yet. Ask for access."
    : /rate limit/i.test(message) ? "Too many tries. Wait a minute and try again." : message;

  const open = () => {
    back.innerHTML = user ? `
      <div class="account-sheet" role="dialog" aria-modal="true" aria-label="Account">
        <h2 class="account-title">${esc(user.user_metadata?.full_name || "Your account")}</h2>
        <p class="account-sub">${esc(user.email || "")}</p>
        <button class="account-primary" type="button" data-account="out">Log out</button>
        <button class="account-cancel" type="button" data-account="close">Done</button>
      </div>` : `
      <div class="account-sheet" role="dialog" aria-modal="true" aria-label="Log in or sign up">
        <h2 class="account-title">Log in or sign up</h2>
        <p class="account-sub">Continue with Google, Microsoft or your email</p>
        <button class="account-provider" type="button" data-account="google">${GOOGLE}Continue with Google</button>
        <button class="account-provider" type="button" data-account="azure">${MICROSOFT}Continue with Microsoft</button>
        <div class="account-or"><span>or</span></div>
        <form class="account-email" data-account-form>
          <input type="email" name="email" placeholder="Email" autocomplete="email" required aria-label="Email">
          <button class="account-primary" type="submit">Continue</button>
        </form>
        <p class="account-note" hidden></p>
        <button class="account-cancel" type="button" data-account="close">Cancel</button>
      </div>`;
    back.hidden = false;
    button.setAttribute("aria-expanded", "true");
    if (!configured && !user) note("Accounts are not set up on this site yet.", "is-warn");
    else if (arrival && !user) note(`The link did not log you in: ${plain(arrival)}`, "is-error");  // an expired or used link
    back.querySelector("input, .account-primary")?.focus();
    if (!user) enabled();  // asked now, so a click on a provider knows at once whether it is on
  };

  button.addEventListener("click", open);
  back.addEventListener("click", async (event) => {
    if (event.target === back) return close();
    const act = event.target.closest("[data-account]")?.dataset.account;
    if (!act) return;
    if (act === "close") return close();
    if (!configured) return note("Accounts are not set up on this site yet.", "is-warn");
    try {
      const auth = (await start()).auth;
      if (act === "out") { await auth.signOut(); user = null; changed(); return close(); }
      // a provider the project has not turned on says so here, rather than leading to Supabase's bare error page
      if (!(await enabled())[act]) return note(`${act === "azure" ? "Microsoft" : "Google"} login is not turned on yet. Use your email for now.`, "is-warn");
      const { error } = await auth.signInWithOAuth({ provider: act, options: { redirectTo: here() } });
      if (error) note(plain(error.message), "is-error");
    } catch (error) { note(plain(error.message), "is-error"); }
  });
  back.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!configured) return note("Accounts are not set up on this site yet.", "is-warn");
    const email = new FormData(event.target).get("email");
    try {
      const { error } = await (await start()).auth.signInWithOtp({ email, options: { emailRedirectTo: here() } });
      note(error ? plain(error.message) : `Check ${email} for a link to log in.`, error ? "is-error" : "is-ok");
    } catch (error) { note(plain(error.message), "is-error"); }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !back.hidden) { event.stopPropagation(); close(); }
  }, true);

  Pie.account = {
    configured,
    open,  // the sheet, for a page that asks one to log in before it gives something (a card's data)
    user: () => user,
    client: () => (configured ? start() : Promise.reject(new Error("Accounts are not set up"))),  // the Supabase client, for a page that keeps data (Reports)
  };
  changed();
})();
