const navigation = document.createElement('nav'); navigation.className = 'top-nav'; navigation.setAttribute('aria-label', 'Main navigation');
for (const [label, href] of [['Overview','/'], ['Champions','/champions'], ['Matches','/#matches-section'], ['Lanes','/#lanes']]) {
  const link = document.createElement('a'); link.href = href; link.textContent = label;
  if ((href === '/champions' && location.pathname.startsWith('/champions')) || (href === '/' && location.pathname === '/' && !location.hash) || (href === '/#matches-section' && location.pathname.startsWith('/matches/'))) link.setAttribute('aria-current','page');
  navigation.append(link);
}
document.querySelector('header').append(navigation);
