// script.js
document.addEventListener("DOMContentLoaded", function(){
  const toggle = document.getElementById("mobile-toggle");
  const nav = document.querySelector(".main-nav");
  toggle && toggle.addEventListener("click", function(){
    if(nav.style.display === "flex") nav.style.display = "";
    else nav.style.display = "flex";
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(a=>{
    a.addEventListener('click', function(e){
      const id = this.getAttribute('href');
      if(id && id.startsWith('#') && id.length>1){
        e.preventDefault();
        const el = document.querySelector(id);
        if(el) el.scrollIntoView({behavior:"smooth", block:"start"});
      }
    });
  });

  // Hero parallax-ish effect: subtle movement on scroll
  const hero = document.getElementById("hero");
  if (hero) {
    window.addEventListener("scroll", function(){
      const sc = window.scrollY;
      hero.style.backgroundPositionY = `${50 + sc * 0.05}%`;
    });
  }
});
