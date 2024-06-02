b =_start
exint
message: string "hello, world!"
out_reg: word 0xfffffc
_start:
    or r0, message
    bl =find_len
    mov r1, r0
    and r0, 0
    or r0, message
    bl =print
    halt
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
    cmp r1, 0
    bxz lr
    ldr r2, [=out_reg]
    ldr r3, [r0]
    str r3, [r2]
    sub r1, 1
    add r0, 4
    b =print