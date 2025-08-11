{ pkgs ? import <nixpkgs> {} }:
( pkgs.buildFHSUserEnv {
    name = "pipzone";
    targetPkgs = pkgs: (with pkgs; [
        python312
        python312Packages.pip
        python312Packages.virtualenv
        python312Packages.networkx
        python312Packages.fastapi 
        python312Packages.uvicorn 
        python312Packages.numpy 
        python312Packages.matplotlib 
    ]);
    runScript = "bash";
    profile = "export PYTHONPATH=\"$PYTHONPATH:~/02_projects/001_LCDN/code/lcdn-python/\"";
}).env  
