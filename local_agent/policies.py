from __future__ import annotations


class DeleteGuard:
    """Exige 5 confirmations explicites avant toute suppression de fichier."""

    REQUIRED_CONFIRMATIONS = 5
    TOKEN = "OUI"

    def confirm_delete(self, path_display: str) -> bool:
        print()
        print("!!! SUPPRESSION DE FICHIER DEMANDÉE !!!")
        print(f"  Cible : {path_display}")
        print(
            f"  Tu dois taper exactement « {self.TOKEN} » "
            f"{self.REQUIRED_CONFIRMATIONS} fois de suite pour autoriser."
        )
        print("  Tape autre chose ou Entrée vide pour annuler.")
        print()
        for i in range(1, self.REQUIRED_CONFIRMATIONS + 1):
            raw = input(f"  Confirmation {i}/{self.REQUIRED_CONFIRMATIONS} : ").strip()
            if raw != self.TOKEN:
                print("  Annulé : confirmation refusée ou incorrecte.")
                return False
        print("  Les 5 confirmations sont enregistrées : suppression autorisée pour ce fichier.")
        return True
