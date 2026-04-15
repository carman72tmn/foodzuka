path = '/root/foodzuka/backend/app/services/iiko_sync_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the literal backslash-n with a real newline
# Looking at the previous output, it was literally "class IikoSyncService:\n"
content = content.replace('class IikoSyncService:\\n', 'class IikoSyncService:\n')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Syntax fix applied.")
