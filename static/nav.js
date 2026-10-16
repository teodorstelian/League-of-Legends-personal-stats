const navigation = document.createElement('nav'); navigation.className = 'top-nav'; navigation.setAttribute('aria-label', 'Main navigation');
for (const [label, href] of [['Overview','/'], ['Champions','/champions'], ['Tier List','/tier-list'], ['Trends','/trends'], ['Matches','/matches']]) {
  const link = document.createElement('a'); link.href = href; link.textContent = label;
  if (href === '/trends' && location.pathname === '/trends') link.setAttribute('aria-current','page');
  if ((href === '/champions' && location.pathname.startsWith('/champions')) || (href === '/tier-list' && location.pathname === '/tier-list') || (href === '/' && location.pathname === '/' && !location.hash) || (href === '/matches' && location.pathname.startsWith('/matches'))) link.setAttribute('aria-current','page');
  navigation.append(link);
}
document.querySelector('header').append(navigation);
