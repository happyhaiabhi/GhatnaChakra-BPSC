/* today's date line on the books screen
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
      (function(){
        var el=document.getElementById('books-date');
        try{
          var today=new Date().toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long',year:'numeric'});
          el.textContent='🌸 '+today+' · Bloom one chapter at a time';
        }catch(e){}
      })();
    