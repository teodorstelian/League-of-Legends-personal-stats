const navigation = document.createElement('nav'); navigation.className = 'top-nav'; navigation.setAttribute('aria-label', 'Main navigation');
for (const [label, href] of [['Overview','/'], ['Draft','/draft'], ['Duo','/duo'], ['Champions','/champions'], ['Tier List','/tier-list'], ['Trends','/trends'], ['Early game','/early-game'], ['Calibration','/calibration'], ['Matches','/matches']]) {
  const link = document.createElement('a'); link.href = href; link.textContent = label;
  if (href === '/draft' && location.pathname === '/draft') link.setAttribute('aria-current','page');
  if (href === '/trends' && location.pathname === '/trends') link.setAttribute('aria-current','page');
  if (href === '/calibration' && location.pathname === '/calibration') link.setAttribute('aria-current','page');
  if ((href === '/champions' && location.pathname.startsWith('/champions')) || (href === '/tier-list' && location.pathname === '/tier-list') || (href === '/' && location.pathname === '/' && !location.hash) || (href === '/matches' && location.pathname.startsWith('/matches'))) link.setAttribute('aria-current','page');
  if (href === '/early-game' && location.pathname === href) link.setAttribute('aria-current','page');
  if (href === '/duo' && location.pathname === href) link.setAttribute('aria-current','page');
  navigation.append(link);
}
document.querySelector('header').append(navigation);

const profileBar = document.createElement('div'); profileBar.className = 'profile-switcher';
const profileLabel = document.createElement('label'); profileLabel.textContent = 'PROFILE';
const profileSelect = document.createElement('select'); profileSelect.setAttribute('aria-label', 'Active profile');
const profileAdd = document.createElement('button'); profileAdd.textContent = '+ Add profile'; profileAdd.type = 'button';
const profileStatus = document.createElement('span'); profileStatus.setAttribute('role', 'status');
profileLabel.append(profileSelect); profileBar.append(profileLabel, profileAdd, profileStatus);
document.querySelector('header').after(profileBar);
async function chooseProfile(riotId) {
  profileSelect.disabled = true; profileAdd.disabled = true; profileStatus.textContent = 'Switching…';
  try {
    const response = await fetch('/api/profiles/select', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({riotId})});
    const result = await response.json(); if (!response.ok) throw Error(result.message || 'Unable to select profile.');
    // Match IDs belong to the previous profile; start the new profile at its overview.
    location.assign('/');
  } catch (error) { profileStatus.textContent = error.message; profileSelect.disabled = false; profileAdd.disabled = false; }
}
profileSelect.addEventListener('change', () => chooseProfile(profileSelect.value));
profileAdd.addEventListener('click', () => { const id = window.prompt('Enter an EUNE Riot ID (Name#Tag)'); if (id?.trim()) chooseProfile(id.trim()); });
fetch('/api/profiles').then(async response => { if(!response.ok) throw Error('Unable to load profiles.'); return response.json(); }).then(body => {
  for(const profile of body.profiles){const option=document.createElement('option');option.value=profile.riotId;option.textContent=`${profile.riotId} · ${profile.region}`;profileSelect.append(option);}
  profileSelect.value=body.active;
}).catch(error => {profileStatus.textContent=error.message;});
