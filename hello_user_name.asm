b =_start
b =_int_handler
ask: string "What is your name?"
hello: string "Hello, "
vosck: string "!"
name: allocate 16
name_address: word 0
name_entered: word 0
out_register: word 0xfffffc
in_register: word 0xfffffd
_start:
    and r0, 0
    or r0, ask
    bl =print

    and r0, 0
    or r0, hello
    bl =print
    
    and r0, 0
    or r0, name
loop2:
    ldr r1, [=name_entered]
    cmp r1, 0
    bz =loop2
    and r0, 0
    or r0, name
    bl =print
    and r0,0
    or r0, vosck
    bl =print
    halt
_int_handler:
    push r0
    push r1
    push r2

    ldr r0, [=in_register]
    ldr r1, [=name_address]
    cmp r1, 0
    orz r1, name
    ldr r2, [r0]
    str r2, [r1]
    cmp r2, 0
    strz r0, [=name_entered]
    or r2, -1
    str r2, [r0]
    add r1, 4
    str r1, [=name_address]

    pop r2
    pop r1
    pop r0
    exint
find_len:
    mov r1, r0
    and r0, 0
loop:
    ldr r2, [r1]
    cmp r2, 0
    bxz lr
    add r0, 1
    add r1, 4
    b =loop
print:
    push r0
    push lr
    bl =find_len
    pop lr
    mov r1, r0
    pop r0
    cmp r1, 0
    bxz lr
    ldr r2, [=out_register]
    ldr r3, [r0]
    cmp r3, 0
    str r3, [r2]
    sub r1, 1
    add r0, 4
    b =print