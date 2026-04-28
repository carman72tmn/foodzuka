-- Создание таблиц для VK Бота (уведомления сотрудников)

CREATE TABLE IF NOT EXISTS vk_bot_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vk_user_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX (vk_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vk_bot_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vk_bot_account_group_links (
    account_id INT NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY (account_id, group_id),
    FOREIGN KEY (account_id) REFERENCES vk_bot_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES vk_bot_groups(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vk_bot_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    delivery_mode ENUM('realtime', 'interval') NOT NULL DEFAULT 'realtime',
    interval_minutes INT NOT NULL DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES vk_bot_accounts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vk_bot_message_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    vk_message_id BIGINT NULL,
    event_type VARCHAR(100) NULL,
    text TEXT NOT NULL,
    status ENUM('pending', 'sent', 'delivered', 'read', 'failed') NOT NULL DEFAULT 'pending',
    error_text TEXT NULL,
    created_at DATETIME NOT NULL,
    sent_at DATETIME NULL,
    FOREIGN KEY (account_id) REFERENCES vk_bot_accounts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
