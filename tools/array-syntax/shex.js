// Parse ShExC with a variant built by run.sh into $WORK/run/<variant>: require('./shex.js')('B0')(text) -> ShExJ
const path = require('path');
module.exports = function load(variant) {
  const P = require(path.resolve(process.env.WORK, 'run', variant, 'shex-parser.js'));
  return function parse(text, base = 'http://a.example/') {
    return P.construct(base, {}, {}).parse(text);
  };
};
