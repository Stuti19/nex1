import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
    apiKey: "AIzaSyDbV-ZWkdlxCe0ZF292MtktP6ang02O_44",
    authDomain: "compoundn-9ab19.firebaseapp.com",
    projectId: "compoundn-9ab19",
    storageBucket: "compoundn-9ab19.firebasestorage.app",
    messagingSenderId: "693090646341",
    appId: "1:693090646341:web:f2c40951e4a84eb26ea62c",
    measurementId: "G-ENQWYHQ0SN"
  };

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export default app; 