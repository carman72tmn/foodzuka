/**
 * This is an advanced example for creating icon bundles for Iconify SVG Framework.
 *
 * It creates a bundle from:
 * - All SVG files in a directory.
 * - Custom JSON files.
 * - Iconify icon sets.
 * - SVG framework.
 *
 * This example uses Iconify Tools to import and clean up icons.
 * For Iconify Tools documentation visit https://docs.iconify.design/tools/tools2/
 */
import { promises as fs } from 'node:fs';
import { dirname, join } from 'node:path';
// Installation: npm install --save-dev @iconify/tools @iconify/utils @iconify/json @iconify/iconify
import { cleanupSVG, importDirectory, isEmptyColor, parseColors, runSVGO } from '@iconify/tools';
import { getIcons, getIconsCSS, stringToIcon } from '@iconify/utils';
const sources = {
    svg: [],
    icons: [],
    json: [
        {
            filename: require.resolve('@iconify-json/bx/icons.json'),
            icons: ["abacus", "accessibility", "add-to-queue", "adjust", "alarm", "alarm-add", "alarm-exclamation", "alarm-off", "alarm-snooze", "album", "align-justify", "align-left", "align-middle", "align-right", "analyse", "anchor", "angry", "aperture", "arch", "archive", "archive-in", "archive-out", "area", "arrow-back", "arrow-from-bottom", "arrow-from-left", "arrow-from-right", "arrow-from-top", "arrow-to-bottom", "arrow-to-left", "arrow-to-right", "arrow-to-top", "at", "atom", "award", "badge", "badge-check", "baguette", "ball", "band-aid", "bar-chart", "bar-chart-alt", "bar-chart-alt-2", "bar-chart-square", "barcode", "barcode-reader", "baseball", "basket", "bell", "bell-off", "bell-plus", "bell-ring", "bolt-circle", "bot", "bowl-rice", "briefcase", "broadcast", "buildings", "bullseye", "bx-bell", "bx-chat", "bx-credit-card", "bx-edit", "bx-gift", "bx-globe", "bx-link-external", "bx-money", "bx-receipt", "bx-wallet", "bx-x-circle", "bxs-star", "bxs-star-half", "bxs-x-circle", "cake", "calendar", "calendar-event", "calendar-x", "car", "caret-down", "cart", "cart-add", "chat", "check", "check-circle", "check-double", "check-shield", "chevron-down", "chevron-left", "chevron-right", "chevron-up", "chevrons-left", "chevrons-right", "circle", "cloud-download", "cloud-upload", "code-alt", "cog", "coin", "comment", "comment-detail", "copy", "credit-card", "cycling", "devices", "dollar", "dots-vertical-rounded", "down-arrow-alt", "download", "drink", "droplet", "edit", "envelope", "error", "error-circle", "food-menu", "ghost", "gift", "git-commit", "globe", "group", "heart", "help-circle", "hide", "history", "home", "id-card", "info-circle", "layer", "link", "link-alt", "link-external", "list-check", "list-plus", "list-ul", "loader-alt", "lock", "lock-open", "log-out", "map", "map-alt", "map-pin", "menu", "menu-alt-left", "message-detail", "message-rounded-dots", "message-square-detail", "minus", "minus-circle", "mobile", "mobile-alt", "mobile-vibration", "money", "moon", "move-vertical", "navigation", "package", "paper-plane", "paperclip", "pause", "pencil", "phone", "phone-call", "pin", "pizza", "play", "plug", "plus", "plus-circle", "printer", "purchase-tag", "purchase-tag-alt", "qr", "qr-scan", "question-mark", "radio-circle", "radio-circle-marked", "receipt", "refresh", "ruble", "run", "save", "search", "search-alt-2", "send", "server", "share-alt", "shield-quarter", "shield-x", "shopping-bag", "show", "skip-next", "skip-previous", "slider-alt", "smile", "speaker", "spin", "star", "stop", "stop-circle", "stopwatch", "store", "store-alt", "subdirectory-right", "sun", "sync", "time", "time-five", "transfer", "trash", "trending-up", "up-arrow-alt", "upload", "user", "user-circle", "user-plus", "user-x", "volume-full", "volume-low", "volume-mute", "wallet", "wallet-alt", "window-alt", "x", "x-circle"],
        },
        {
            filename: require.resolve('@iconify-json/bxl/icons.json'),
            icons: ["android", "facebook", "github", "google", "linkedin", "telegram", "twitter", "vk", "whatsapp", "windows"],
        },
        {
            filename: require.resolve('@iconify-json/bxs/icons.json'),
            icons: ["alarm", "bell", "bell-ring", "car", "circle", "pin", "star", "star-half", "volume-full", "x-circle"],
        },
        {
            filename: require.resolve('@iconify-json/mdi/icons.json'),
            icons: ["account", "account-circle-outline", "account-clock", "account-details", "account-multiple", "account-multiple-outline", "account-off", "alert", "alert-circle", "alert-circle-outline", "alert-octagon", "alert-thick", "api", "arrow-expand-all", "basket", "bell", "bell-cog-outline", "bell-off-outline", "bell-outline", "bell-plus-outline", "bell-ring", "bell-ring-outline", "bike", "bullhorn", "bullhorn-outline", "bullhorn-variant", "cancel", "cellphone-message", "chart-bar", "chart-line", "check", "check-circle", "check-circle-outline", "checkbox-blank-outline", "checkbox-marked", "circle-small", "clock-edit", "clock-outline", "close", "close-circle", "cog", "cog-outline", "cogs", "content-copy", "content-save", "currency-rub", "delete", "delete-outline", "delete-sweep", "delete-sweep-outline", "eye", "eye-off", "eye-outline", "file-document-edit-outline", "file-upload", "filter", "folder", "folder-sync", "food", "food-apple", "food-apple-outline", "food-fork-drink", "food-variant", "format-list-bulleted", "gamepad-variant", "gift-outline", "history", "home", "information", "information-outline", "key", "key-off", "keyboard-outline", "layers-outline", "link-variant", "loading", "lock-check-outline", "lock-open-variant-outline", "login", "logout", "magnify", "map-marker-alert", "map-marker-check", "map-marker-edit", "map-search-outline", "message-arrow-left", "message-arrow-right", "message-bulleted", "message-processing-outline", "message-search-outline", "message-text", "message-text-outline", "minus-box", "open-in-new", "package-variant-closed", "pause", "pencil", "pencil-outline", "phone", "play", "plus", "plus-circle", "radiobox-blank", "radiobox-marked", "refresh", "refresh-circle", "robot", "robot-industrial-outline", "robot-outline", "server", "shape-outline", "star", "star-circle", "storefront-outline", "subdirectory-arrow-right", "sync", "telegram", "ticket-percent", "truck-delivery", "truck-delivery-outline", "tune-vertical", "variable", "view-list-outline", "vk", "whatsapp"],
        },
        {
            filename: require.resolve('@iconify-json/ri/icons.json'),
            icons: ["add-circle-line", "add-line", "arrow-left-s-line", "arrow-right-s-line", "bank-card-line", "bar-chart-2-line", "bar-chart-box-line", "bar-chart-line", "book-open-line", "building-line", "chat-check-line", "checkbox-circle-line", "close-circle-line", "close-line", "code-line", "coin-line", "dashboard-line", "delete-bin-line", "download-line", "drag-move-2-fill", "e-bike-2-line", "edit-circle-line", "edit-line", "error-warning-fill", "error-warning-line", "external-link-line", "eye-line", "file-copy-line", "file-list-3-line", "filter-3-line", "folder-line", "folder-open-line", "gift-line", "group-line", "history-line", "id-card-line", "image-add-line", "inbox-line", "information-line", "mail-line", "mail-send-line", "map-pin-2-line", "map-pin-line", "message-2-line", "message-3-line", "notification-3-line", "notification-line", "phone-fill", "phone-line", "price-tag-3-line", "refresh-line", "save-line", "search-line", "send-plane-line", "settings-3-line", "settings-4-line", "share-line", "shield-check-line", "shield-keyhole-line", "shield-user-line", "shopping-bag-3-line", "shopping-bag-line", "shopping-basket-line", "shopping-cart-2-line", "spam-line", "star-line", "sync-line", "telegram-fill", "telegram-line", "tools-line", "truck-line", "upload-line", "user-add-line", "user-line", "user-received-line", "user-search-line", "user-settings-line", "vk-fill", "whatsapp-line"],
        },
        {
            filename: require.resolve('@iconify-json/fa/icons.json'),
            icons: ["circle"],
        }
    ],
};
// File to save bundle to
const target = join(__dirname, 'icons.css');
(async function () {
    // Create directory for output if missing
    const dir = dirname(target);
    try {
        await fs.mkdir(dir, {
            recursive: true,
        });
    }
    catch (err) {
        //
    }
    const allIcons = [];
    /**
     * Convert sources.icons to sources.json
     */
    if (sources.icons) {
        const sourcesJSON = sources.json ? sources.json : (sources.json = []);
        // Sort icons by prefix
        const organizedList = organizeIconsList(sources.icons);
        for (const prefix in organizedList) {
            const filename = require.resolve(`@iconify/json/json/${prefix}.json`);
            sourcesJSON.push({
                filename,
                icons: organizedList[prefix],
            });
        }
    }
    /**
     * Bundle JSON files and collect icons
     */
    if (sources.json) {
        for (let i = 0; i < sources.json.length; i++) {
            const item = sources.json[i];
            // Load icon set
            const filename = typeof item === 'string' ? item : item.filename;
            const content = JSON.parse(await fs.readFile(filename, 'utf8'));
            for (const key in content) {
                if (key === 'prefix' && content.prefix === 'tabler') {
                    for (const k in content.icons)
                        content.icons[k].body = content.icons[k].body.replace(/stroke-width="2"/g, 'stroke-width="1.5"');
                }
            }
            // Filter icons
            if (typeof item !== 'string' && item.icons?.length) {
                const filteredContent = getIcons(content, item.icons);
                if (!filteredContent)
                    throw new Error(`Cannot find required icons in ${filename}`);
                // Collect filtered icons
                allIcons.push(filteredContent);
            }
            else {
                // Collect all icons from the JSON file
                allIcons.push(content);
            }
        }
    }
    /**
     * Bundle custom SVG icons and collect icons
     */
    if (sources.svg) {
        for (let i = 0; i < sources.svg.length; i++) {
            const source = sources.svg[i];
            // Import icons
            const iconSet = await importDirectory(source.dir, {
                prefix: source.prefix,
            });
            // Validate, clean up, fix palette, etc.
            await iconSet.forEach(async (name, type) => {
                if (type !== 'icon')
                    return;
                // Get SVG instance for parsing
                const svg = iconSet.toSVG(name);
                if (!svg) {
                    // Invalid icon
                    iconSet.remove(name);
                    return;
                }
                // Clean up and optimise icons
                try {
                    // Clean up icon code
                    await cleanupSVG(svg);
                    if (source.monotone) {
                        // Replace color with currentColor, add if missing
                        // If icon is not monotone, remove this code
                        await parseColors(svg, {
                            defaultColor: 'currentColor',
                            callback: (attr, colorStr, color) => {
                                return !color || isEmptyColor(color) ? colorStr : 'currentColor';
                            },
                        });
                    }
                    // Optimise
                    await runSVGO(svg);
                }
                catch (err) {
                    // Invalid icon
                    console.error(`Error parsing ${name} from ${source.dir}:`, err);
                    iconSet.remove(name);
                    return;
                }
                // Update icon from SVG instance
                iconSet.fromSVG(name, svg);
            });
            // Collect the SVG icon
            allIcons.push(iconSet.export());
        }
    }
    // Generate CSS from collected icons
    const cssContent = allIcons
        .map(iconSet => getIconsCSS(iconSet, Object.keys(iconSet.icons), {
        iconSelector: '.{prefix}-{name}',
        mode: 'mask',
    }))
        .join('\n');
    // Save the CSS to a file
    await fs.writeFile(target, cssContent, 'utf8');
    console.log(`Saved CSS to ${target}!`);
})().catch(err => {
    console.error(err);
});
/**
 * Sort icon names by prefix
 */
function organizeIconsList(icons) {
    const sorted = Object.create(null);
    icons.forEach(icon => {
        const item = stringToIcon(icon);
        if (!item)
            return;
        const prefix = item.prefix;
        const prefixList = sorted[prefix] ? sorted[prefix] : (sorted[prefix] = []);
        const name = item.name;
        if (!prefixList.includes(name))
            prefixList.push(name);
    });
    return sorted;
}
