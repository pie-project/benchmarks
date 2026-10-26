window.Pie = window.Pie || {};

// The site's accounts, kept by Supabase Auth (supabase.com): Google, Microsoft and an emailed link, with no server of
// the site's own. Fill in the project's URL and its public anon key (Project Settings → API); both are meant to be
// public, as every visitor's browser uses them. (Project Settings → API Keys: the Publishable key; older projects call it
// the anon public key, under Legacy API keys.) Left empty, Log in opens its sheet and says accounts are not set up yet.
//
// In the Supabase project: Authentication → Providers, turn on Google and Azure (Microsoft) with their client IDs, and
// Email with "magic link"; Authentication → URL Configuration, add the site's address (https://benchmarks.pie-project.org
// and http://127.0.0.1:8765 for local work) to the redirect URLs.
Pie.authConfig = {
  url: "https://lehcljutthlrgkisxtya.supabase.co",
  anonKey: "sb_publishable_rpi6T2wvhoesslqfi-UDyQ_LkCl0sf9",  // the project's publishable key: public, as every visitor's browser uses it
};
