let syncState;
if(!document.querySelector('#refresh[data-check-history]'))document.getElementById('refresh').addEventListener('click',()=>command('check'));
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
    if(document.querySelector('.library-toolbar')) {
      const status=document.getElementById('sync-status');status.title=status.textContent;
      const state=syncState.status==='syncing'?'Importing…':syncState.status==='waiting'||syncState.status==='error'?syncState.message:'Manual sync · Refresh to update';
      status.textContent=`${syncState.saved} games · ${state}${syncState.exhausted?' · All available history imported':''}`;
    }
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
document.getElementById('sync-more').addEventListener('click', () => command('more'));
updateSync();
setInterval(updateSync, 4000);
