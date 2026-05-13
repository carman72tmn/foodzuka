import { h } from 'vue'
import { Icon } from '@iconify/vue'
import checkboxChecked from '@images/svg/checkbox-checked.svg'
import checkboxIndeterminate from '@images/svg/checkbox-indeterminate.svg'
import checkboxUnchecked from '@images/svg/checkbox-unchecked.svg'
import radioChecked from '@images/svg/radio-checked.svg'
import radioUnchecked from '@images/svg/radio-unchecked.svg'

const customIcons = {
  'mdi-checkbox-blank-outline': checkboxUnchecked,
  'mdi-checkbox-marked': checkboxChecked,
  'mdi-minus-box': checkboxIndeterminate,
  'mdi-radiobox-marked': radioChecked,
  'mdi-radiobox-blank': radioUnchecked,
}

const aliases = {
  calendar: 'bx-calendar',
  collapse: 'bx-chevron-up',
  complete: 'bx-check',
  cancel: 'bx-x',
  close: 'bx-x',
  delete: 'bx-bxs-x-circle',
  clear: 'bx-x-circle',
  success: 'bx-check-circle',
  info: 'bx-info-circle',
  warning: 'bx-error',
  error: 'bx-error-circle',
  prev: 'bx-chevron-left',
  ratingEmpty: 'bx-star',
  ratingFull: 'bx-bxs-star',
  ratingHalf: 'bx-bxs-star-half',
  next: 'bx-chevron-right',
  delimiter: 'bx-circle',
  sort: 'bx-up-arrow-alt',
  expand: 'bx-chevron-down',
  menu: 'bx-menu',
  subgroup: 'bx-caret-down',
  dropdown: 'bx-chevron-down',
  edit: 'bx-pencil',
  loading: 'bx-refresh',
  first: 'bx-skip-previous',
  last: 'bx-skip-next',
  unfold: 'bx-move-vertical',
  file: 'bx-paperclip',
  plus: 'bx-plus',
  minus: 'bx-minus',
  sortAsc: 'bx-up-arrow-alt',
  sortDesc: 'bx-down-arrow-alt',
}

export const iconify = {
  component: props => {
    let iconName = props.icon

    // Normalize icon name for Iconify API
    // mdi-cog -> mdi:cog, ri-tools-line -> ri:tools-line, bx-home -> bx:home
    if (typeof iconName === 'string') {
      const parts = iconName.split('-')
      if (parts.length > 1) {
        const prefix = parts[0]
        const knownPrefixes = ['mdi', 'ri', 'bx', 'bxl', 'bxs', 'fa', 'line-md', 'tabler']
        if (knownPrefixes.includes(prefix)) {
          // Join the rest with hyphen
          iconName = `${prefix}:${parts.slice(1).join('-')}`
        }
      }
      
      // Load custom SVG directly
      const iconComponent = customIcons[props.icon]
      if (iconComponent)
        return h(iconComponent)
    }

    return h(Icon, {
      ...props,
      icon: iconName,
    })
  },
}
export const icons = {
  defaultSet: 'iconify',
  aliases,
  sets: {
    iconify,
  },
}
