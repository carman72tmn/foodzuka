$content = Get-Content -Raw "C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\configs\nginx\default.conf"
$content | ssh vezuroll "cat > /root/foodzuka/configs/nginx/default.conf"
