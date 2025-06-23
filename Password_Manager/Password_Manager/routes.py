import os
import signal
import logging
import sqlite3
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import check_password_hash, generate_password_hash

from .services import UserManager, PasswordService
from .core.password_generator import PasswordGenerator
from .core.cryptography import CryptographyManager
from .database import DatabaseManager
from config import Config

# Inizializza il blueprint
main = Blueprint('main', __name__)

# --- NUOVO: Gestore di errori globale ---
# Questa funzione catturerà tutti gli errori non gestiti (bug) nell'applicazione.
@main.app_errorhandler(500)
def handle_internal_server_error(e):
    """Gestisce gli errori 500 (Internal Server Error) in modo centralizzato."""
    # Registra l'errore completo nel log per il debug da parte dello sviluppatore.
    logging.error(f"Errore del server non gestito: {e}", exc_info=True)
    # Mostra una pagina di errore generica e user-friendly all'utente.
    return render_template("500.html"), 500

# Decoratori per l'autenticazione
def login_required(f):
    """Decoratore per richiedere l'autenticazione."""
    def decorated_function(*args, **kwargs):
        if 'utente_id' not in session or 'user_password' not in session:
            flash('Per favore, effettua il login per accedere a questa pagina.', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# Route dell'applicazione
@main.route('/')
def index():
    """Pagina principale - reindirizza al login o dashboard."""
    if 'utente_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    """Gestisce il login degli utenti."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username e password sono obbligatori', 'error')
            return render_template('login.html')
        
        user = UserManager.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session['utente_id'] = user['id']
            session['username'] = user['username']
            session['user_password'] = password
            flash('Accesso effettuato con successo!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username o password non validi', 'error')
    
    return render_template('login.html')


@main.route('/registrazione', methods=['GET', 'POST'])
def registrazione():
    """Gestisce la registrazione di nuovi utenti."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('conferma_password', '')
        
        if not username or not password:
            flash('Username e password sono obbligatori', 'error')
            return render_template('registrazione.html')
        
        if password != confirm_password:
            flash('Le password non corrispondono', 'error')
            return render_template('registrazione.html')
        
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            flash(f'La password deve essere di almeno {Config.MIN_PASSWORD_LENGTH} caratteri', 'error')
            return render_template('registrazione.html')
        
        try:
            if UserManager.create_user(username, password):
                flash('Registrazione completata! Ora puoi effettuare il login', 'success')
                return redirect(url_for('main.login'))
            else: # Questo else non viene mai raggiunto a causa del try/except sottostante, ma lo teniamo per chiarezza.
                flash('Username già esistente', 'error')
        except sqlite3.IntegrityError:
            # Errore SPECIFICO: l'username è già presente (violazione del vincolo UNIQUE).
            flash('Username già esistente. Per favore, scegline un altro.', 'error')
    
    return render_template('registrazione.html')


@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale con elenco password."""
    try:
        master_key = UserManager.get_master_key(session['utente_id'], session['user_password'])
        password_list = PasswordService.get_user_passwords(session['utente_id'], master_key)
        return render_template('dashboard.html', password_salvate=password_list)
        
    except ValueError as e:
        # Errore SPECIFICO: molto probabilmente un errore di decrittografia su una o più password.
        logging.error(f"Errore di decrittografia per l'utente {session['utente_id']}: {e}")
        flash('Errore durante la decrittografia di una o più password salvate. Verifica la tua password master o contatta il supporto.', 'error')
        # Il logout qui è una scelta di design: se la master key non funziona, l'utente deve riloggarsi.
        return redirect(url_for('main.logout'))


@main.route('/aggiungi', methods=['GET', 'POST'])
@login_required
def aggiungi_password():
    """Aggiunge una nuova password."""
    form_data = {}
    if request.method == 'POST':
        # ... la logica per il generatore di password rimane invariata ...
        if 'genera_password' in request.form:
            length = int(request.form.get('lunghezza', 16))
            use_special_chars = 'caratteri_speciali' in request.form
            use_uppercase = 'usa_maiuscole' in request.form
            use_numbers = 'usa_numeri' in request.form
            password_generata = PasswordGenerator.generate_secure_password(length=length, use_special_chars=use_special_chars, use_uppercase=use_uppercase, use_numbers=use_numbers)
            form_data = {
                'nome_sito': request.form.get('nome_sito', ''), 'username_sito': request.form.get('username_sito', ''), 'password_sito': password_generata,
                'lunghezza': length, 'caratteri_speciali': use_special_chars, 'usa_maiuscole': use_uppercase, 'usa_numeri': use_numbers
            }
            return render_template('aggiungi.html', form_data=form_data, password_generata=password_generata)
        
        site_name = request.form.get('nome_sito', '').strip()
        site_username = request.form.get('username_sito', '').strip()
        site_password = request.form.get('password_sito', '')
        
        if not site_name or not site_username or not site_password:
            flash('Tutti i campi sono obbligatori', 'error')
            return render_template('aggiungi.html')
        
        try:
            master_key = UserManager.get_master_key(session['utente_id'], session['user_password'])
            
            if PasswordService.add_password(session['utente_id'], site_name, site_username, site_password, master_key):
                flash('Password aggiunta e crittografata con successo!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                # Questo è un caso generico di fallimento dal service layer.
                flash('Errore durante il salvataggio della password.', 'error')
        except ValueError as e:
            # Errore SPECIFICO: fallimento nel derivare la master key.
            logging.error(f"Impossibile derivare la master key per aggiungere una password: {e}")
            flash('Si è verificato un errore di sicurezza. Effettua nuovamente il login.', 'error')
            return redirect(url_for('main.logout'))
        except sqlite3.Error as e:
            # Errore SPECIFICO: errore del database.
            logging.error(f"Errore database durante l'aggiunta di una password: {e}")
            flash('Errore del database. Impossibile salvare la password.', 'error')
    
    return render_template('aggiungi.html', form_data=form_data)


@main.route('/modifica/<int:password_id>', methods=['GET', 'POST'])
@login_required
def modifica_password(password_id):
    """Modifica una password esistente."""
    try:
        master_key = UserManager.get_master_key(session['utente_id'], session['user_password'])
        password_entry_raw = PasswordService.get_password_by_id(password_id, session['utente_id'])
        
        if not password_entry_raw:
            flash('Password non trovata.', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Gestiamo qui l'errore di decrittografia in modo specifico
        try:
            password_decrypted = CryptographyManager.decrypt_password(password_entry_raw['password_sito_encrypted'], master_key)
        except ValueError:
            logging.error(f"Impossibile decifrare la password con ID {password_id} per la modifica.")
            flash('Impossibile decifrare la password per la modifica. La password master potrebbe essere errata.', 'error')
            return redirect(url_for('main.dashboard'))

        password_entry = {'id': password_entry_raw['id'], 'nome_sito': password_entry_raw['nome_sito'], 'username_sito': password_entry_raw['username_sito'], 'password_sito': password_decrypted}
        
        if request.method == 'POST':
            site_name = request.form.get('nome_sito', '').strip()
            site_username = request.form.get('username_sito', '').strip()
            site_password = request.form.get('password_sito', '')
            
            if not site_name or not site_username or not site_password:
                flash('Tutti i campi sono obbligatori.', 'error')
                return render_template('modifica.html', password_entry=password_entry)
            
            if PasswordService.update_password(password_id, session['utente_id'], site_name, site_username, site_password, master_key):
                flash('Password modificata e crittografata con successo!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Errore durante la modifica della password.', 'error')
        
        return render_template('modifica.html', password_entry=password_entry)

    except sqlite3.Error as e:
        logging.error(f"Errore database durante la modifica della password ID {password_id}: {e}")
        flash('Si è verificato un errore del database.', 'error')
        return redirect(url_for('main.dashboard'))


@main.route('/elimina/<int:password_id>')
@login_required
def elimina_password(password_id):
    """Elimina una password."""
    if PasswordService.delete_password(password_id, session['utente_id']):
        flash('Password eliminata con successo!', 'success')
    else:
        flash('Errore durante l\'eliminazione della password.', 'error')
    
    return redirect(url_for('main.dashboard'))


@main.route('/logout')
def logout():
    """Effettua il logout pulendo la sessione."""
    session.clear()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('main.login'))


@main.route('/cambia_password_master', methods=['GET', 'POST'])
@login_required
def cambia_password_master():
    """Cambia la password master dell'utente ri-crittografando tutte le password."""
    if request.method == 'POST':
        current_password = request.form.get('password_attuale', '')
        new_password = request.form.get('nuova_password', '')
        confirm_new_password = request.form.get('conferma_nuova_password', '')
        
        if new_password != confirm_new_password:
            flash('Le nuove password non corrispondono.', 'error')
            return render_template('cambia_password.html')
        
        if len(new_password) < Config.MIN_PASSWORD_LENGTH:
            flash(f'La nuova password deve essere di almeno {Config.MIN_PASSWORD_LENGTH} caratteri.', 'error')
            return render_template('cambia_password.html')
        
        user = UserManager.get_user_by_id(session['utente_id'])
        if not user or not check_password_hash(user['password_hash'], current_password):
            flash('Password attuale non corretta.', 'error')
            return render_template('cambia_password.html')
        
        try:
            # Questa operazione è critica e va eseguita come una transazione
            with DatabaseManager.get_connection() as conn:
                old_master_key = UserManager.get_master_key(session['utente_id'], current_password)
                saved_passwords = conn.execute('SELECT * FROM password_salvate WHERE utente_id = ?', (session['utente_id'],)).fetchall()
                
                passwords_decrypted = []
                for row in saved_passwords:
                    password_decrypted = CryptographyManager.decrypt_password(row['password_sito_encrypted'], old_master_key)
                    passwords_decrypted.append({'id': row['id'], 'password': password_decrypted})
                
                new_salt = CryptographyManager.generate_salt()
                new_password_hash = generate_password_hash(new_password)
                new_master_key = CryptographyManager.derive_key(new_password, new_salt)
                
                conn.execute('UPDATE utenti SET password_hash = ?, encryption_salt = ? WHERE id = ?', (new_password_hash, new_salt, session['utente_id']))
                
                for pwd_data in passwords_decrypted:
                    new_encrypted_password = CryptographyManager.encrypt_password(pwd_data['password'], new_master_key)
                    conn.execute('UPDATE password_salvate SET password_sito_encrypted = ? WHERE id = ?', (new_encrypted_password, pwd_data['id']))
                
                # Il commit è gestito automaticamente dal context manager 'with'. Se c'è un errore, viene fatto un rollback.
            
            session['user_password'] = new_password
            flash('Password master cambiata con successo! Tutte le password sono state ri-crittografate.', 'success')
            return redirect(url_for('main.dashboard'))
            
        except ValueError as e:
            logging.error(f"Errore di decrittografia durante il cambio della master password: {e}")
            flash('Errore durante la decrittografia delle vecchie password. Operazione annullata.', 'error')
        except sqlite3.Error as e:
            logging.error(f"Errore database durante il cambio della master password: {e}")
            flash('Errore del database. Operazione annullata.', 'error')
            
        return render_template('cambia_password.html')
    
    return render_template('cambia_password.html')


@main.route('/genera_password', methods=['GET', 'POST'])
@login_required
def genera_password():
    """Pagina dedicata per la generazione di password."""
    password_generata = None
    if request.method == 'POST':
        length = int(request.form.get('lunghezza', 16))
        use_special_chars = request.form.get('caratteri_speciali') == 'on'
        use_uppercase = request.form.get('usa_maiuscole', 'on') == 'on'
        use_numbers = request.form.get('usa_numeri', 'on') == 'on'
        password_generata = PasswordGenerator.generate_secure_password(length=length, use_special_chars=use_special_chars, use_uppercase=use_uppercase, use_numbers=use_numbers)
    return render_template('genera_password.html', password=password_generata)


@main.route('/shutdown')
@login_required
def shutdown():
    """Spegne il server (solo per richieste locali)."""
    if request.remote_addr in ('127.0.0.1', 'localhost', '::1'):
        os.kill(os.getpid(), signal.SIGINT)
        return "Server in fase di spegnimento..."
    return "Operazione non permessa", 403