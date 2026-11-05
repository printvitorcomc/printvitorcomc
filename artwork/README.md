# Fontes do cabeçalho

O perfil carrega somente os WebP renderizados em `assets/`. O SVG original está preservado, sem alterações, em `source/ascii-profile.svg.txt`; a extensão de texto evita sua prévia como imagem. O gerador original continua em `scripts/build-ascii.py`.

O loop mantém 864 × 200 pixels, dez segundos, transparência, versões clara/escura e uma alternativa estática para a preferência de movimento reduzido. A exportação usa 16 FPS, acompanhando a rotação original; as trocas de caracteres continuam a 8 FPS.

Para gerar novamente, instale Python 3, Node.js, a fonte Courier New/Courier e `sharp@0.35.5`, e execute na raiz:

```sh
python3 scripts/render-ascii.py
node scripts/encode-ascii.cjs
```

O segundo comando aceita `--compare` para gerar também um GIF de comparação em `previews/`. Os quadros intermediários ficam em `.ascii-frames/` e não são versionados.
