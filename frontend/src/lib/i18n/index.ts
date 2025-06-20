import { register, init, getLocaleFromNavigator, locale as currentLocaleStore } from 'svelte-i18n';

import enTranslations from './en'
import esTranslations from './es'

register('en', () => Promise.resolve(enTranslations));
register('es', () => Promise.resolve(esTranslations));

const getInitialLocale = (): string => {
    if (typeof window !== 'undefined') {
        const storeLocale = localStorage.getItem('app-locale');
        if (storeLocale) {
            return storeLocale;
        }
    }
    return getLocaleFromNavigator()?.split('-')[0] || 'es';
}



init({
    fallbackLocale: 'es',
    initialLocale: getLocaleFromNavigator()
});

export function setLocale(newLocale: string): void {
    console.log(newLocale);
    if (typeof window !== 'undefined') {
        localStorage.setItem('app-locale', newLocale);
        document.documentElement.lang = newLocale; // et Lang attribute on HTML Element
    }
    currentLocaleStore.set(newLocale);

}

export { currentLocaleStore as locale }