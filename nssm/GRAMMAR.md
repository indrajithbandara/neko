# NSSM Grammar

Notations used:

- `UPPERCASE` identifiers generally signify atomic elements, unless otherwise
    specified.
- `lowercase` identifiers generally signify terms. These consist of patterns of
    atomic elements, and other terms. These are defined in `lowercase` and
    referred to from there on as `<lowercase>`.
- `x ::= expr` - the term `x` is defined as `expr`.
- `[x]` - a literal character x.
- `[xyz]` - either a literal x, y or z.
- `[x-y]` - signifies a range of x to y.
- `x ::= a b c` - the term `x` is defined as `a` then `b` then `c`
- `x ::= (a b) | c` - the term `x` is defined as either `a` followed by `b`,
    or as `c`.
- `x?` - `x` zero or one times.
- `x+` - `x` one or more times.
- `x*` - equivalent to `x?+`, that is, `x` zero or more times.
- `"null"` - the literal string `null`.

## Primitive value tokens
These are the most atomic factors that you can have. These are the blocks
for building more complicated factors and structures.

The following token types will be defined further down in this section.

```
     val_token  ::= <decimal_int>
                  | <real>
                  | <binary_int>
                  | <octal_int>
                  | <hex_int>
                  | <string>
                  | <null>
                  | <identifier>.
```

### Identifiers
These are names that should be resolved at runtime. These can be variables,
or functions, or builtin calls. If these do not exist in the interpretation
stage, then a NameError should be raised, however, we must not perform this
validation before this stage.

```
    identifier  ::= [a-zA-Z_] [a-zA-Z0-9_$]*.
```

### Misc

```
          null  ::=  "null".
```

### Integer types
```                    
         digit  ::=  [0-9].
  decimal_uint  ::=  <digit>+.   
   decimal_int  ::=  [+-]? <decimal_uint>.
                     
                     
 real_mantissa  ::=  <decimal_int>? "." <decimal_uint>+.
 real_exponent  ::=  [Ee] <decimal_int>.
          real  ::=  <real_mantissa> <real_exponent>?.
                     
                     
  binary_digit  ::=  [01].
    binary_int  ::=  [+-]? "0" [Bb] <binary_digit>+.
                     
                     
   octal_digit  ::=  [0-7].
     octal_int  ::=  [+-]? "0" [Oo] <octal_digit>+.
                     
                     
     hex_digit  ::=  <digit> | [A-F] | [a-f].
       hex_int  ::=  [+-]? "0" [Xx] <hex_digit>+.
```

### String types
We will not support a singular-character class. There is little point.

Assume that **`CHAR`** represents any __UTF-8__ character **EXCEPT** for
`\`, `'`, and `"` which are special case characters handled separately.
**`LINE_FEED_CHAR`** represents a literal `\n` character. 
```
    utf8_descr  ::=  [ N ] [ { ] <alphanum>+ [ } ].

    escape_seq  ::=  "\'"                   -- ' escape
                   | "\""                   -- " escape        
                   | "\\"                   -- \ escape
                   | "\t"                   -- horizontal tab
                   | "\r"                   -- carriage return
                   | "\n"                   -- line feed
                   | "\u" <digit>+          -- UTF-8 escape sequence
                   | "\" <utf8_descr>       -- UTF-8 description
                   | "\" LINE_FEED_CHAR.  
         
 raw_character  ::=  <escape_seq> | CHAR.
    
   string_body  ::=  <raw_character>*.
   
        string  ::=  ['] <string_body> [']
                   | ["] <string_body> ["].
```

## Atomic operators

```
 int_divide_ass ::= "//=".
        pow_ass ::= "**=".
        bsr_ass ::= ">>=".
        bsl_ass ::= "<<=".
            inc ::= "++".
            dec ::= "--".
       plus_ass ::= "+=".
      minus_ass ::= "-=".
      times_ass ::= "*=".
     divide_ass ::= "/=".
     modulo_ass ::= "%=".
             ne ::= "!=". 
            pow ::= "**".
     int_divide ::= "//".
            bsl ::= "<<".
            bsr ::= ">>".
             eq ::= "==".
            lte ::= "<=".
            gte ::= ">=".
       band_ass ::= "&=".
       bxor_ass ::= "^=".
        bor_ass ::= "|=".
            lor ::= "||".
           land ::= "&&".
           
       question ::= "?".
          colon ::= ":".     
           plus ::= "+".
          minus ::= "-".
         modulo ::= "%".
           bang ::= "!".
          tilde ::= "~".
          times ::= "*".
         divide ::= "/".
             lt ::= "<".
             gt ::= ">".
            ass ::= "=".
           band ::= "&".
            bor ::= "|".
           bxor ::= "^".
          comma ::= ",".           
```

## Compounds

### Arguments

These consist of one or more factors, each separated by a comma. 
```
           args ::= <factor>            
                  | <factor> <comma> <args>.
```
Parameters are pretty much the same, except can only consist of identifiers.
```         
         params ::= <identifier>
                  | <identifier> <comma> <params>.
```

### Collections

```
          tuple ::= "(" <factor> <comma> <args>? ")".                
           list ::= "[" <args>? "]".
            set ::= "{" <args>? "}".                             
                                                                 
     collection ::= <tuple> | <list> | <set>.                     
```

### Expressions

These are expected to output something at the end.

Function calls, indexes and slices:
```    
  function_call ::= "(" <args> ")".
          index ::= "[" <decimal_int> "]".
          slice ::= "[" <decimal_int> <colon> <decimal_int>? "]"
                  | "[" <colon> <decimal_int>? "]".   

```
Atomic values:
```
         atomic ::= <val_token> | <collection> | <function> | <factor>.

        postfix ::= <factor> <inc>
                  | <factor> <dec>            
                  | <factor> <pow> <factor>
                  | <factor> <function_call>
                  | <factor> <index>
                  | <factor> <slice>.
        
         prefix ::= <inc> <factor>
                  | <dec> <factor>
                  | <plus> <factor>
                  | <minus> <factor>
                  | <bang> <factor>
                  | <tilde> <factor>.
         
           mult ::= <factor> <times> <factor>
                  | <factor> <int_divide> <factor>
                  | <factor> <divide> <factor>
                  | <factor> <modulo> <factor>.
           
            add ::= <factor> <plus> <factor>
                  | <factor> <minus> <factor>.
                  
       bitshift ::= <factor> <bsl> <factor>
                  | <factor> <bsr> <factor>.
           
           comp ::= <factor> <lte> <factor>
                  | <factor> <gte> <factor>
                  | <factor> <lt> <factor>
                  | <factor> <gt> <factor>.
             
       equality ::= <factor> <eq> <factor>
                  | <factor> <ne> <factor>.
             
        bit_and ::= <factor> <band> <factor>.
             
        bit_xor ::= <factor> <bxor> <factor>.
                  
         bit_or ::= <factor> <bor> <factor>. 
 
    logical_and ::= <factor> <land> <factor>.
                  
     logical_or ::= <factor> <lor> <factor>.
                  
     assignment ::= <identifier> <ass> <factor>
                  | <identifier> <int_divide_ass> <factor>
                  | <identifier> <pow_ass> <factor>       
                  | <identifier> <bsl_ass> <factor>       
                  | <identifier> <bsr_ass> <factor>       
                  | <identifier> <plus_ass> <factor>       
                  | <identifier> <minus_ass> <factor>       
                  | <identifier> <times_ass> <factor>       
                  | <identifier> <divide_ass> <factor>       
                  | <identifier> <modulo_ass> <factor>       
                  | <identifier> <band_ass> <factor>       
                  | <identifier> <bxor_ass> <factor>       
                  | <identifier> <bor_ass> <factor>.       
          
         factor ::= "(" <atomic> ")"
                  | <assignment>
                  | <logical_or>
                  | <logical_and>
                  | <bit_or>
                  | <bit_xor>
                  | <bit_and>
                  | <equality>
                  | <comp>
                  | <bitshift>
                  | <add>
                  | <mult>
                  | <prefix>
                  | <postfix>.                  
```
## Statements
Statements can consist of statement groups or factors, and thus do not have to
output an actual value.
```
      statement ::= <statement_group> | <condition> | <while> | <factor>.
      
statement_group ::= "{" (<statement> (LINE_FEED | <semi>))* "}".

           else ::= "else" <statement>.

      condition ::= "if" "(" <factor> ")" <statement>
                  | <condition> <else>.
                  
          while ::= "while" "(" <factor> ")" <statement>.
```
Functions are basically lambdas. To make stuff simpler, we do not allow
one-lined lambdas without braces.
```
       function ::= "("  <params>?  ")" <statement_group>.
```

## Scripts
Scripts can be zero or more statements. They are executed top-down.
```
         script ::= <statement>*.
```

I think this is everything. My head hurts from thinking about this so much.