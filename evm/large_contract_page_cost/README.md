Study the cost of pages when executing a large contract.

The contract contains of multiple pages.  The code will jump to next page to try to evict caches.  The code likes like

page_dst0:
    PUSH4 $page1_dst0
    JUMP
page0_dst1:
    JUMPDEST
    PUSH3 $page1_dst1
    JUMP  
page0_dst2:
    ...

page1_dst0: // offset 4K
    JUMPDEST
    PUSH3 $page2_dst0
    JUMP
page1_dst1:
    JUMPDEST
    PUSH3 $page2_dst1
    JUMP

...

pageN_dst0: // offset N * 4K

...

pageM_dst0: // last page
    JUMPDEST
    PUSH3 $page0_dst1
    JUMP
...
pageM_dstL: // last code segment
    JUMPDEST
    PUSH0
    PUSH0
    RETURN
