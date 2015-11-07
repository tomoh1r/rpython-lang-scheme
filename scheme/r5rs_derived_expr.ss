(define-syntax cond
  (syntax-rules (else =>)
    ((cond (else result1 result2 ...))
     (begin result1 result2 ...))
    ((cond (test => result))
     (let ((temp test))
       (if temp (result temp))))
    ((cond (test => result) clause1 clause2 ...)
     (let ((temp test))
       (if temp
           (result temp)
           (cond clause1 clause2 ...))))
    ((cond (test)) test)
    ((cond (test) clause1 clause2 ...)
     (let ((temp test))
       (if temp
           temp
           (cond clause1 clause2 ...))))
    ((cond (test result1 result2 ...))
     (if test (begin result1 result2 ...)))
    ((cond (test result1 result2 ...)
           clause1 clause2 ...)
     (if test
         (begin result1 result2 ...)
         (cond clause1 clause2 ...)))))

(define-syntax and
  (syntax-rules ()
    ((and) #t)
    ((and test) test)
    ((and test1 test2 ...)
     (if test1 (and test2 ...) #f))))

(define-syntax or
  (syntax-rules ()
    ((or) #f)
    ((or test) test)
    ((or test1 test2 ...)
     (let ((x test1))
       (if x x (or test2 ...))))))

(define-syntax case
  (syntax-rules (else)
;;; XXX this check does not work yet
;    ((case (key ...) clauses ...)
;     (let ((atom-key (key ...)))
;       (case atom-key clauses ...)))
    ((case key (else expr1 expr2 ...))
     (begin expr1 expr2 ...))
    ((case key ((atoms ...) expr1 expr2 ...))
     (if (memv key '(atoms ...))
         (begin expr1 expr2 ...)))
    ((case key ((atoms ...) expr1 expr2 ...) clause2 clause3 ...)
     (if (memv key '(atoms ...))
         (begin expr1 expr2 ...)
         (case key clause2 clause3 ...)))))
