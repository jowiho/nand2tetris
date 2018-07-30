// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

//for i = RO; i > 0; i--
//  n += R1
//r2 = n

    @n
    M=0
    @R0
    D=M
    @i
    M=D

(LOOP)
    @i
    D=M
    @STOP
    D;JEQ  // if i == 0 goto STOP

    @R1
    D=M
    @n
    M=M+D // n += R1

    @i
    M=M-1  // i--

    @LOOP
    0;JMP

(STOP)
    @n
    D=M
    @R2
    M=D  // R2 = n

(END)
    @END
    0;JMP