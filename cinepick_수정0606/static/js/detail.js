/* =============================================
   detail.js — 영화 상세 페이지 인터랙션
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

  // ─── 1. 탭 전환 ──────────────────────────────
  const tabs      = document.querySelectorAll('.cp-detail-tabs .cp-tab');
  const panels    = document.querySelectorAll('.cp-tab-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.target;

      // 탭 active 전환
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // 패널 전환
      panels.forEach(p => {
        p.classList.remove('active');
        if (p.id === target) p.classList.add('active');
      });
    });
  });


  // ─── 2. 줄거리 더보기 ─────────────────────────
  const synopsisWrap = document.querySelector('.cp-synopsis-text');
  const moreBtn      = document.querySelector('.cp-synopsis-more');

  if (moreBtn && synopsisWrap) {
    moreBtn.addEventListener('click', () => {
      const expanded = synopsisWrap.classList.toggle('expanded');
      moreBtn.childNodes[0].textContent = expanded ? '접기 ' : '더보기 ';
    });
  }


  // ─── 3. 찜하기 토글 ───────────────────────────
  const wishlistBtn = document.querySelector('.cp-wishlist-btn');

  if (wishlistBtn) {
    wishlistBtn.addEventListener('click', () => {
      const isActive = wishlistBtn.classList.toggle('active');
      const icon     = wishlistBtn.querySelector('i');

      if (isActive) {
        icon.classList.remove('fa-regular');
        icon.classList.add('fa-solid');
        wishlistBtn.innerHTML = '<i class="fa-solid fa-heart"></i> 찜 완료';
      } else {
        wishlistBtn.innerHTML = '<i class="fa-regular fa-heart"></i> 찜하기';
      }
    });
  }


  // ─── 4. 별점 선택 (리뷰 작성) ─────────────────
  const starBtns = document.querySelectorAll('.cp-star-select i');

  starBtns.forEach((star, index) => {
    // 마우스 올릴 때
    star.addEventListener('mouseover', () => {
      starBtns.forEach((s, i) => {
        s.classList.toggle('active', i <= index);
      });
    });

    // 마우스 나갈 때 — 선택된 값 유지
    star.addEventListener('mouseleave', () => {
      const selected = document.querySelector('.cp-star-select').dataset.selected ?? -1;
      starBtns.forEach((s, i) => {
        s.classList.toggle('active', i <= Number(selected));
      });
    });

    // 클릭으로 확정
    star.addEventListener('click', () => {
      document.querySelector('.cp-star-select').dataset.selected = index;
      starBtns.forEach((s, i) => {
        s.classList.toggle('active', i <= index);
      });
    });
  });

  // 마우스가 별점 영역 전체를 나갈 때
  const starWrap = document.querySelector('.cp-star-select');
  if (starWrap) {
    starWrap.addEventListener('mouseleave', () => {
      const selected = starWrap.dataset.selected ?? -1;
      starBtns.forEach((s, i) => {
        s.classList.toggle('active', i <= Number(selected));
      });
    });
  }


  // ─── 5. 리뷰 좋아요 토글 ──────────────────────
  document.querySelectorAll('.cp-review-item__likes').forEach(btn => {
    btn.addEventListener('click', () => {
      const countEl = btn.querySelector('.like-count');
      if (!countEl) return;

      const isLiked  = btn.dataset.liked === 'true';
      const count    = parseInt(countEl.textContent, 10);
      btn.dataset.liked     = !isLiked;
      countEl.textContent   = isLiked ? count - 1 : count + 1;

      const icon = btn.querySelector('i');
      icon.classList.toggle('fa-regular', isLiked);
      icon.classList.toggle('fa-solid',   !isLiked);
      btn.style.color = isLiked ? '' : 'var(--accent)';
    });
  });


  // ─── 6. 미니 리뷰 좋아요 (줄거리 탭) ──────────
  document.querySelectorAll('.cp-mini-review__likes').forEach(el => {
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => {
      const icon  = el.querySelector('i');
      const isOn  = el.dataset.liked === 'true';
      el.dataset.liked = !isOn;
      icon.classList.toggle('fa-regular', isOn);
      icon.classList.toggle('fa-solid',   !isOn);
    });
  });


  // ─── 7. 평점 바 애니메이션 (Intersection Observer) ─
  const bars = document.querySelectorAll('.cp-rating-bar-fill');

  if (bars.length) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const bar    = entry.target;
          const width  = bar.style.width; // 이미 인라인으로 지정되어 있음
          bar.style.width = '0';
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              bar.style.width = width;
            });
          });
          observer.unobserve(bar);
        }
      });
    }, { threshold: 0.2 });

    bars.forEach(bar => observer.observe(bar));
  }


  // ─── 8. 리뷰 작성 제출 (임시) ────────────────
  const reviewSubmitBtn = document.querySelector('#review-submit');
  const reviewTextarea  = document.querySelector('.cp-review-textarea');

  if (reviewSubmitBtn && reviewTextarea) {
    reviewSubmitBtn.addEventListener('click', () => {
      const text = reviewTextarea.value.trim();
      if (!text) {
        reviewTextarea.focus();
        reviewTextarea.style.borderColor = 'var(--accent)';
        setTimeout(() => {
          reviewTextarea.style.borderColor = '';
        }, 1500);
        return;
      }

      // 실제 구현 시 AJAX로 서버에 전송
      console.log('[리뷰 제출]', text);
      reviewTextarea.value = '';
      const starWrapEl = document.querySelector('.cp-star-select');
      if (starWrapEl) {
        delete starWrapEl.dataset.selected;
        starBtns.forEach(s => s.classList.remove('active'));
      }
    });
  }

});
