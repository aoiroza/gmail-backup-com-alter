{
  description = "Gmail Backup - backup and restore your Gmail mailbox over IMAP";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      src = nixpkgs.lib.fileset.toSource {
        root = ./.;
        fileset = nixpkgs.lib.fileset.unions [
          ./gmb.py
          ./gmail-backup.py
          ./gmail-backup-gui.py
          ./gmb.gif
          ./gmb.ico
          ./messages
          ./README
          ./LICENSE
        ];
      };

      mkGmailBackup = pkgs: { gui ? false }:
        let
          python = if gui
            then pkgs.python3.withPackages (ps: [ ps.wxpython ])
            else pkgs.python3;
        in
        pkgs.stdenvNoCC.mkDerivation {
          pname = if gui then "gmail-backup-gui" else "gmail-backup";
          version = "0.12347";
          inherit src;

          nativeBuildInputs = [ pkgs.makeWrapper ]
            ++ pkgs.lib.optionals (gui && pkgs.stdenv.hostPlatform.isLinux) [ pkgs.wrapGAppsHook3 ];
          buildInputs = pkgs.lib.optionals (gui && pkgs.stdenv.hostPlatform.isLinux) [ pkgs.gtk3 ];
          dontWrapGApps = true;

          installPhase = ''
            runHook preInstall
            share=$out/share/gmail-backup
            mkdir -p $share $out/bin
            cp -r gmb.py gmail-backup.py gmail-backup-gui.py gmb.gif gmb.ico messages $share/
            makeWrapper ${python.interpreter} $out/bin/gmail-backup \
              --add-flags $share/gmail-backup.py
          '' + pkgs.lib.optionalString gui ''
            makeWrapper ${python.interpreter} $out/bin/gmail-backup-gui \
              --add-flags $share/gmail-backup-gui.py \
              ''${gappsWrapperArgs[@]}
          '' + ''
            runHook postInstall
          '';

          meta = {
            description = "Backup and restore of your Gmail mailbox over IMAP";
            license = pkgs.lib.licenses.gpl3Plus;
            mainProgram = if gui then "gmail-backup-gui" else "gmail-backup";
            platforms = pkgs.lib.platforms.all;
          };
        };
    in
    {
      packages = forAllSystems (pkgs: rec {
        gmail-backup = mkGmailBackup pkgs { };
        gmail-backup-gui = mkGmailBackup pkgs { gui = true; };
        default = gmail-backup;
      });

      apps = forAllSystems (pkgs: {
        default = {
          type = "app";
          program = "${self.packages.${pkgs.system}.gmail-backup}/bin/gmail-backup";
        };
        gui = {
          type = "app";
          program = "${self.packages.${pkgs.system}.gmail-backup-gui}/bin/gmail-backup-gui";
        };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ (pkgs.python3.withPackages (ps: [ ps.wxpython ])) ];
        };
      });
    };
}
