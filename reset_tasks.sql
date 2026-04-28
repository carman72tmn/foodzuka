UPDATE sync_statuses 
SET status = 'error', details = 'Задача прервана из-за перезапуска сервера' 
WHERE status = 'running';
