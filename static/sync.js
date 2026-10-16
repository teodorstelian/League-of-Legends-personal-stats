let syncState;
async function updateSync() {
  try {
    const response = await fetch('/api/sync');
    if (!response.ok) throw new Error();
    const previousCount = syncState?.saved;
    const previousDetails = syncState?.details;
    syncState = await response.json();
    if (previousCount !== undefined && (previousCount !== syncState.saved || previousDetails !== syncState.details) && !document.getElementById('refresh').disabled) load();
    const oldest = syncState.oldest ? ` · Oldest: ${new Date(syncState.oldest).toLocaleDateString()}` : '';
    document.getElementById('sync-status').textContent = `${syncState.saved} saved / ${syncState.target} target · ${syncState.details} with advanced details${oldest} · ${syncState.exhausted ? 'End of available history. ' : ''}${syncState.message}`;
    document.getElementById('sync-toggle').textContent = syncState.paused ? 'Resume sync' : 'Pause sync';
    document.getElementById('sync-more').disabled = syncState.exhausted;
  } catch { document.getElementById('sync-status').textContent = 'Unable to check sync status. Retrying…'; }
}
async function command(action) {
  try {
    const response = await fetch(`/api/sync/${action}`, {method: 'POST'});
    if (!response.ok) throw new Error();
    await updateSync();
  } catch { document.getElementById('sync-status').textContent = 'Unable to update sync. Please try again.'; }
}
document.getElementById('sync-toggle').addEventListener('click', () => command(syncState?.paused ? 'resume' : 'pause'));
document.getElementById('sync-more').addEventListener('click', () => command('more'));
updateSync();
setInterval(updateSync, 4000);
