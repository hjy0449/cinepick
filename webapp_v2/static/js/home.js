/* =============================================
   home.js — 메인 페이지 인터랙션
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

  // ─── 1. Swiper Coverflow (인기 영화) ───────
  const coverflowSwiper = new Swiper('.cp-coverflow-swiper', {
    effect: 'coverflow',
    grabCursor: true,
    centeredSlides: true,
    slidesPerView: 5,
    loop: true,

    autoplay: {
      delay: 2500,        // 2.5초마다 넘어가요
      disableOnInteraction: false,  // 손으로 넘겨도 자동재생 유지
      pauseOnMouseEnter: true,
    },

    coverflowEffect: {
      rotate: 30,
      stretch: 0,
      depth: 100,
      modifier: 1,
      slideShadows: false,
    },
    pagination: {
      el: '.cp-coverflow-pagination',
      clickable: true,
    },
  });


  // ─── 2. AI 추천 영화 — 그리드 스크롤 ────────
  // (그리드가 10개 카드 2줄로 되어 있으므로
  //  좌우 화살표로 스크롤되는 방식)
  const aiCarousel  = document.getElementById('ai-carousel');
  const aiPrev      = document.getElementById('ai-prev');
  const aiNext      = document.getElementById('ai-next');

  if (aiCarousel && aiPrev && aiNext) {
    const scrollStep = () => {
      // 카드 1개 너비 + gap 기준 스크롤
      const card = aiCarousel.querySelector('.cp-ai-card');
      if (!card) return 0;
      return card.offsetWidth + 16;
    };

    aiPrev.addEventListener('click', () => {
      aiCarousel.scrollBy({ left: -scrollStep() * 2, behavior: 'smooth' });
    });

    aiNext.addEventListener('click', () => {
      aiCarousel.scrollBy({ left:  scrollStep() * 2, behavior: 'smooth' });
    });
  }


  // ─── 3. 커뮤니티 탭 전환 ──────────────────
  const tabs = document.querySelectorAll('.cp-community .cp-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      // 실제 데이터 전환은 백엔드 연동 후 AJAX로 처리 가능
    });
  });

});
