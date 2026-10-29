ssh vezuroll "docker exec -i foodtech-backend python -c 'import app.services.vk_token_manager as tm; print(tm.VK_API_VERSION)'"
