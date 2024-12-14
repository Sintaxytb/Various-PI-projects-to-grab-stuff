import os
import re
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import cpu_count

# Variables globales
site_results = {}  # Dictionnaire pour stocker les résultats par site
processed_size = 0  # Taille traitée en Go
message_lock = threading.Lock()  # Créer un verrou pour gérer l'affichage des messages


# Fonction pour écrire lettre par lettre avec un délai de 0.05s
def write_slowly(text, delay=0.05, color_code='\033[31m', newline=True):
    with message_lock:  # Assurer qu'un seul thread écrit à la fois
        colored_text = f"{color_code}{text}\033[0m"  # Appliquer la couleur avant d'afficher le texte
        for char in colored_text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)  # Délai entre chaque caractère
        if newline:
            sys.stdout.write("\n")  # Ajoute un saut de ligne à la fin du message


# Afficher le logo
def display_logo():
    logo = f"""
\033[31m    
 █████╗  █████╗ ███╗   ███╗██████╗  █████╗    ██████╗███████╗  █████╗ ██████╗  █████╗ ██╗  ██╗███████╗██████╗
██╔══██╗██╔══██╗████╗ ████║██╔══██╗██╔══██╗   ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔════╝██╔══██╗
██║  ╚═╝██║  ██║██╔████╔██║██████╦╝██║  ██║   ╚█████╗ █████╗  ███████║██████╔╝██║  ╚═╝███████║█████╗  ██████╔╝
██║  ██╗██║  ██║██║╚██╔╝██║██╔══██╗██║  ██║    ╚═══██╗██╔══╝  ██╔══██║██╔══██╗██║  ██╗██╔══██║██╔══╝  ██╔══██╗
╚█████╔╝╚█████╔╝██║ ╚═╝ ██║██████╦╝╚█████╔╝   ██████╔╝███████╗██║  ██║██║  ██║╚█████╔╝██║  ██║███████╗██║  ██║
 ╚════╝  ╚════╝ ╚═╝     ╚═╝╚═════╝  ╚════╝    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    """
    print("\033[31m" + logo)


# Fonction pour nettoyer le nom de fichier
def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)


# Fonction pour calculer la taille totale des fichiers dans un dossier
def get_total_size_in_gb(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    return total_size / (1024 ** 3)  # Convertir octets en Go


# Lecture des sites ciblés à partir du fichier
def sites():
    with open("targetedSites.txt", encoding='utf-8') as websites:
        return [site.strip() for site in websites if not site.startswith("!")]


# Liste les fichiers dans le dossier "ULP_Dumps"
def list_files_in_folder():
    return [item for item in os.listdir("ULP_Dumps") if
            os.path.isfile(os.path.join("ULP_Dumps", item)) and item.endswith(".txt")]


# Crée un dossier de destination avec la date actuelle
def create_target_directory():
    date_str = datetime.now().strftime("%Y-%m-%d")
    target_dir = f"TargetedCombos/Target_{date_str}"
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


# Fonction pour générer des combos et les écrire dans des fichiers pour chaque site
def combogen(site, file, target_dir, progress_callback):
    global processed_size
    local_count = 0
    sanitized_site = sanitize_filename(site)

    try:
        file_path = os.path.join("ULP_Dumps", file)
        processed_size += os.path.getsize(file_path) / (1024 ** 3)  # Convertir en Go

        # Charger toutes les lignes en mémoire
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Filtrer les lignes pertinentes pour ce site
        valid_lines = []
        for line in lines:
            if site in line:
                sp = line.split(":")
                if len(sp) < 2:
                    continue
                user_ = sp[-2].strip()
                pass_ = sp[-1].strip()

                # Éviter les URL et valider la ligne
                if any(prefix in user_ for prefix in ["http://", "https://", "www."]):
                    continue
                valid_lines.append(f"{user_}:{pass_}\n")
                local_count += 1

        # Écrire toutes les lignes valides en une seule fois
        output_file = os.path.join(target_dir, f"{sanitized_site}_combos.txt")
        with open(output_file, "a", encoding='utf-8') as out_file:
            out_file.writelines(valid_lines)

        progress_callback(site, local_count)

    except Exception as e:
        write_slowly(f"Erreur dans le traitement du fichier {file} pour {site} : {e}", newline=True)


# Fonction pour supprimer les lignes contenant des formats invalides
def remove_invalid_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        filtered_lines = [line for line in lines if re.match(r'^[^|]*:[^|]*$', line.strip())]

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(filtered_lines)
        write_slowly(f"Le fichier {file_path} a été nettoyé.", newline=True)
    except Exception as e:
        write_slowly(f"Erreur lors du nettoyage de {file_path} : {e}", newline=True)


# Fonction pour mettre à jour les résultats en temps réel sur la ligne spécifique à chaque site
def update_results(site, count):
    site_results[site]['accounts'] += count
    with message_lock:  # Assurer qu'un seul thread modifie l'affichage à la fois
        sys.stdout.write(f"\033[31m\r[{site}] Comptes trouvés : {site_results[site]['accounts']}")
        sys.stdout.flush()  # Forcer l'affichage immédiat


# Fonction pour traiter un site
def process_site(site, target_dir):
    global site_results
    site_results[site] = {'accounts': 0, 'errors': 0, 'duration': 0}

    start_time = time.time()
    write_slowly(f"\033[31mCiblage en cours pour {site}...", newline=True)

    for file in list_files_in_folder():
        combogen(site, file, target_dir, update_results)

    for file in os.listdir(target_dir):
        if file.endswith(".txt"):
            remove_invalid_lines(os.path.join(target_dir, file))

    site_results[site]['duration'] = time.time() - start_time


# Affichage du récapitulatif final
def display_summary():
    write_slowly("\033[31m\nRécapitulatif Final :", newline=True)
    total_accounts = sum(result['accounts'] for result in site_results.values())
    total_duration = sum(result['duration'] for result in site_results.values())

    for site, result in site_results.items():
        write_slowly(f"\033[31m{site} : {result['accounts']} comptes trouvés, {result['duration']:.2f}s", newline=True)

    write_slowly(f"\033[31mTotal des comptes trouvés : {total_accounts}", newline=True)
    write_slowly(f"\033[31mTaille totale traitée : {processed_size:.2f} Go", newline=True)


# Fonction principale
def main():
    display_logo()  # Affiche le logo
    total_size_gb = get_total_size_in_gb("ULP_Dumps")
    write_slowly(f"\033[31mTaille totale des fichiers dans 'ULP_Dumps': {total_size_gb:.2f} Go", delay=0.1,
                 newline=True)

    target_dir = create_target_directory()

    # Utiliser ProcessPoolExecutor pour le traitement en parallèle sur plusieurs cœurs
    max_workers = cpu_count() * 2  # Doubler le nombre de processus pour maximiser l'utilisation du CPU
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_site, site, target_dir): site for site in sites()}
        for future in as_completed(futures):
            future.result()

    display_summary()
    write_slowly("\033[31mTraitement terminé avec succès!", delay=0.1, newline=True)


if __name__ == "__main__":
    main()
