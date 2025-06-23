// Eseguiamo tutto il codice solo dopo che il contenuto HTML della pagina è stato completamente caricato.
document.addEventListener('DOMContentLoaded', () => {

    // --- FUNZIONI UTILITY PER I POPUP (deduplicate) ---

    function showPopup(message, category = 'success') {
        const container = document.getElementById('flash-container');
        if (!container) return;

        const popup = document.createElement('div');
        let classes = 'flash-message text-base font-normal leading-normal rounded-lg p-4 shadow-md transition-transform transform translate-x-full opacity-0';

        if (category === 'error') {
            classes += ' bg-[#f8d7da] text-[#721c24]';
        } else if (category === 'info') {
            classes += ' bg-[#d1deed] text-[#0d141c]';
        } else { // 'success'
            classes += ' bg-[#d1deed] text-[#0d141c]';
        }

        popup.className = classes;
        popup.textContent = message;
        container.appendChild(popup);

        setTimeout(() => {
            popup.classList.remove('translate-x-full', 'opacity-0');
            popup.classList.add('translate-x-0', 'opacity-100');
        }, 100);

        const duration = category === 'info' ? 5000 : 3000;
        setTimeout(() => {
            popup.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => popup.remove(), 300);
        }, duration);
    }

    // --- LOGICA SPECIFICA PER LE PAGINE ---

    // Logica per la pagina di REGISTRAZIONE
    const registrationForm = document.querySelector('form[action="/registrazione"]');
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('conferma_password');
            let hasError = false;

            if (password.value.length > 0 && password.value.length < 8) {
                hasError = true;
                showPopup('La password deve essere di almeno 8 caratteri', 'error');
            }
            if (password.value && confirmPassword.value && password.value !== confirmPassword.value) {
                hasError = true;
                showPopup('Le password non corrispondono', 'error');
            }
            if (hasError) event.preventDefault();
        });
    }

    // Logica per la pagina CAMBIA PASSWORD MASTER
    const changeMasterPasswordForm = document.querySelector('form[action="/cambia_password_master"]');
    if (changeMasterPasswordForm) {
        showPopup('Attenzione: Cambiando la password master, tutte le password salvate verranno ri-crittografate.', 'info');
        changeMasterPasswordForm.addEventListener('submit', function(event) {
            // Logica di validazione simile a quella della registrazione...
        });
    }
    
    // Logica per la pagina DASHBOARD
    const dashboardTable = document.querySelector('table'); // Un modo per identificare la dashboard
    if (dashboardTable) {
        // Aggiungiamo gli event listener ai bottoni usando la delegazione di eventi per efficienza
        dashboardTable.addEventListener('click', function(event) {
            const target = event.target.closest('button');
            if (!target) return;

            // Logica per Mostra/Nascondi password
            if (target.id.startsWith('toggle-btn-')) {
                const id = target.id.replace('toggle-btn-', '');
                const hiddenElement = document.getElementById('password-' + id);
                const visibleElement = document.getElementById('password-visible-' + id);
                const toggleText = target.querySelector('span'); // Cerca lo span dentro il bottone

                if (hiddenElement.classList.contains('hidden')) {
                    hiddenElement.classList.remove('hidden');
                    visibleElement.classList.add('hidden');
                    toggleText.textContent = 'Mostra';
                } else {
                    hiddenElement.classList.add('hidden');
                    visibleElement.classList.remove('hidden');
                    toggleText.textContent = 'Nascondi';
                }
            }
            
            // Logica per Copia password
            if (target.id.startsWith('copy-btn-')) {
                const passwordToCopy = target.dataset.password;
                navigator.clipboard.writeText(passwordToCopy).then(() => {
                    const originalText = target.textContent;
                    target.textContent = 'Copiato!';
                    setTimeout(() => { target.textContent = originalText; }, 2000);
                });
            }
        });
    }

    // Logica per la pagina GENERA PASSWORD
    const copyGeneratedBtn = document.getElementById('copy-generated-btn');
    if (copyGeneratedBtn) {
        copyGeneratedBtn.addEventListener('click', function() {
            const passwordInput = document.getElementById("generated-password");
            navigator.clipboard.writeText(passwordInput.value).then(() => {
                showPopup('Copiato con successo!', 'success');
                const originalText = this.textContent;
                this.textContent = 'Copiato!';
                setTimeout(() => { this.textContent = originalText; }, 2000);
            });
        });
    }

 // --- LOGICA PER LA PAGINA AGGIUNGI PASSWORD ---
    const toggleBtn = document.getElementById('toggle-generator-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const section = document.getElementById('generatore-section');
            if (section) {
                const isVisible = section.style.display !== 'none';
                section.style.display = isVisible ? 'none' : 'block';
            }
        });
    }
    // --- LOGICA PER LA NAVIGAZIONE (EFFETTI HOVER E INDICATORE) ---
    const navLinks = document.querySelectorAll('.nav-link');
    const navIndicator = document.getElementById('nav-indicator');

    if (navLinks.length > 0 && navIndicator) {
        let activeLink = null;

        // Trova il link attivo in base all'URL corrente
        navLinks.forEach(link => {
            if (link.href === window.location.href) {
                activeLink = link;
                link.classList.add(...link.dataset.activeClass.split(' '));
                link.classList.remove(...link.dataset.inactiveClass.split(' '));
            } else {
                link.classList.add(...link.dataset.inactiveClass.split(' '));
                link.classList.remove(...link.dataset.activeClass.split(' '));
            }
        });

        // Funzione per posizionare l'indicatore
        const moveIndicator = (element) => {
            if (!element) {
                navIndicator.style.width = '0';
                return;
            };
            const linkRect = element.getBoundingClientRect();
            const navRect = element.parentElement.getBoundingClientRect();
            navIndicator.style.width = `${linkRect.width}px`;
            navIndicator.style.height = `${linkRect.height}px`;
            navIndicator.style.left = `${linkRect.left - navRect.left}px`;
            navIndicator.style.top = `${linkRect.top - navRect.top}px`;
        };

        // Posiziona l'indicatore sul link attivo al caricamento della pagina
        moveIndicator(activeLink);

        // Aggiungi gli eventi per l'hover
        navLinks.forEach(link => {
            // Effetto di sollevamento al passaggio del mouse
            link.addEventListener('mouseenter', () => {
                link.style.transform = 'translateY(-1px)';
                moveIndicator(link); // Sposta l'indicatore sul link in hover
            });

            // Rimuovi l'effetto di sollevamento e riposiziona l'indicatore
            link.addEventListener('mouseleave', () => {
                link.style.transform = 'translateY(0)';
                moveIndicator(activeLink); // Riporta l'indicatore sul link attivo
            });
        });
    }

    // Aggiungi qui altre logiche specifiche se necessario...

});