import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';

// PrimeVue
import PrimeVue from 'primevue/config';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ColumnGroup from 'primevue/columngroup';
import Toast from 'primevue/toast';
import ToastService from 'primevue/toastservice';
import Card from 'primevue/card';
import Checkbox from 'primevue/checkbox';
import Menu from 'primevue/menu';
import Chart from 'primevue/chart';

// PrimeVue styles
import 'primevue/resources/themes/lara-light-green/theme.css';
import 'primevue/resources/primevue.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

// Global styles
import './assets/styles/main.scss';

const app = createApp(App);
const pinia = createPinia();

// Utiliser Pinia
app.use(pinia);

// Utiliser Vue Router
app.use(router);

// Utiliser PrimeVue
app.use(PrimeVue, { ripple: true });
app.use(ToastService);

// Enregistrer les composants PrimeVue globalement
app.component('Dialog', Dialog);
app.component('Button', Button);
app.component('InputText', InputText);
app.component('Dropdown', Dropdown);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('ColumnGroup', ColumnGroup);
app.component('Toast', Toast);
app.component('Card', Card);
app.component('Checkbox', Checkbox);
app.component('Menu', Menu);
app.component('Chart', Chart);

// Monter l'application
app.mount('#app');
